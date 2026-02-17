#!/usr/bin/env python3
"""
Import completed human evaluation annotation packs.
Computes summary stats and optionally inter-rater agreement (Cohen's kappa).
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def _cohens_kappa(labels_a: list, labels_b: list) -> float:
    """Compute Cohen's kappa for two raters on categorical labels."""
    if len(labels_a) != len(labels_b) or not labels_a:
        return 0.0

    n = len(labels_a)
    categories = sorted(set(labels_a) | set(labels_b))
    k = len(categories)
    if k == 0:
        return 1.0

    cat_idx = {c: i for i, c in enumerate(categories)}
    matrix = [[0] * k for _ in range(k)]
    for a, b in zip(labels_a, labels_b):
        matrix[cat_idx[a]][cat_idx[b]] += 1

    # observed agreement
    po = sum(matrix[i][i] for i in range(k)) / n

    # expected agreement
    pe = 0.0
    for i in range(k):
        row_sum = sum(matrix[i])
        col_sum = sum(matrix[j][i] for j in range(k))
        pe += (row_sum * col_sum) / (n * n)

    if pe == 1.0:
        return 1.0
    return round((po - pe) / (1.0 - pe), 4)


def _load_pack(path: str) -> list[dict]:
    items = []
    with open(path, "r") as f:
        for line in f:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def _compute_summary(items: list[dict]) -> dict:
    """Compute summary statistics from scored items."""
    scored = [it for it in items if it.get("scores")]

    if not scored:
        return {"error": "No scored items found"}

    g0_values = []
    g1_values = []
    g2_values = []
    u1_values = []
    u2_values = []

    for it in scored:
        s = it["scores"]
        if s.get("G0_ungrounded_present") is not None:
            g0_values.append(bool(s["G0_ungrounded_present"]))
        if s.get("G1_support_ratio") is not None:
            g1_values.append(float(s["G1_support_ratio"]))
        if s.get("G2_citation_correctness") is not None:
            g2_values.append(int(s["G2_citation_correctness"]))
        if s.get("U1_answer_clarity") is not None:
            u1_values.append(int(s["U1_answer_clarity"]))
        if s.get("U2_actionability") is not None:
            u2_values.append(int(s["U2_actionability"]))

    summary = {
        "total_scored": len(scored),
        "ungrounded_rate": round(sum(g0_values) / len(g0_values), 4) if g0_values else None,
        "mean_support_ratio": round(sum(g1_values) / len(g1_values), 4) if g1_values else None,
        "mean_citation_correctness": round(sum(g2_values) / len(g2_values), 4) if g2_values else None,
        "mean_clarity": round(sum(u1_values) / len(u1_values), 4) if u1_values else None,
        "mean_actionability": round(sum(u2_values) / len(u2_values), 4) if u2_values else None,
    }
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Import completed human eval packs and compute summary."
    )
    parser.add_argument("--run_name", required=True,
                        help="Run name for output placement")
    parser.add_argument("--pack", required=True,
                        help="Path to completed annotation pack JSONL (rater A)")
    parser.add_argument("--pack_b", default=None,
                        help="Optional second rater pack for agreement")
    parser.add_argument("--split", default="test",
                        help="Split label for filenames")
    args = parser.parse_args()

    pack_a = _load_pack(args.pack)
    if not pack_a:
        print(f"[!] No items found in {args.pack}")
        sys.exit(1)

    run_dir = Path("results/runs") / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # compute summary for rater A
    summary_a = _compute_summary(pack_a)
    summary = {"rater_a": summary_a}

    # if rater B provided, compute agreement
    if args.pack_b:
        pack_b = _load_pack(args.pack_b)
        if pack_b:
            summary_b = _compute_summary(pack_b)
            summary["rater_b"] = summary_b

            # align by query_id
            b_lookup = {it["query_id"]: it for it in pack_b}
            shared = [
                (a, b_lookup[a["query_id"]])
                for a in pack_a if a["query_id"] in b_lookup
            ]

            if shared:
                # Cohen's kappa for G0
                g0_a = []
                g0_b = []
                for a, b in shared:
                    sa = a.get("scores", {}).get("G0_ungrounded_present")
                    sb = b.get("scores", {}).get("G0_ungrounded_present")
                    if sa is not None and sb is not None:
                        g0_a.append(str(bool(sa)))
                        g0_b.append(str(bool(sb)))

                if g0_a:
                    summary["agreement"] = {
                        "G0_cohens_kappa": _cohens_kappa(g0_a, g0_b),
                        "n_shared": len(shared),
                    }

                # optional: U1 binned kappa (>=3 vs <3)
                u1_a = []
                u1_b = []
                for a, b in shared:
                    sa = a.get("scores", {}).get("U1_answer_clarity")
                    sb = b.get("scores", {}).get("U1_answer_clarity")
                    if sa is not None and sb is not None:
                        u1_a.append("good" if int(sa) >= 3 else "poor")
                        u1_b.append("good" if int(sb) >= 3 else "poor")

                if u1_a:
                    summary["agreement"]["U1_binned_kappa"] = _cohens_kappa(u1_a, u1_b)

            # averaged summary
            avg = {}
            for key in summary_a:
                if key == "total_scored":
                    continue
                va = summary_a.get(key)
                vb = summary_b.get(key)
                if va is not None and vb is not None:
                    avg[key] = round((va + vb) / 2, 4)
            summary["averaged"] = avg

    # write outputs
    summary_path = run_dir / f"human_eval_summary_{args.split}.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[✓] Summary written to {summary_path}")

    # write detailed CSV
    csv_rows = []
    for it in pack_a:
        s = it.get("scores", {})
        csv_rows.append({
            "query_id": it.get("query_id", ""),
            "question": it.get("question", ""),
            "baseline": it.get("baseline", ""),
            "G0": s.get("G0_ungrounded_present", ""),
            "G1": s.get("G1_support_ratio", ""),
            "G2": s.get("G2_citation_correctness", ""),
            "U1": s.get("U1_answer_clarity", ""),
            "U2": s.get("U2_actionability", ""),
            "comments": s.get("comments", ""),
        })

    csv_path = run_dir / f"human_eval_{args.split}.csv"
    pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
    print(f"[✓] Detailed scores written to {csv_path}")


if __name__ == "__main__":
    main()
