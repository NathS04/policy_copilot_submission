"""B4 overlap-threshold tuning (Phase 2 of the residual-gap closure).

Simulates B4 with candidate values of ``b4_overlap_threshold`` over the
retained B4 outputs.jsonl on the **dev split only**, then picks the
largest threshold drop that preserves Abstention Accuracy = 1.0 on the
dev split. Pure recomputation: no LLM calls, no policy code import — the
simulation reproduces the rules in
``src/policy_copilot/service/conservative_hybrid.py`` over the existing
``mode_used``, ``fallback_reason``, ``evidence_strength`` fields.

Outputs:
  results/tables/b4_threshold_tune_dev.csv  (per-candidate metrics)
  prints recommended threshold and projected test-split impact
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_B4_RUN = ROOT / "results/runs/b4_conservative_hybrid_replay_v2_final"
DEFAULT_GOLDEN = ROOT / "eval/golden_set/golden_set_v2_corrected.csv"

# Same rerank floor as the policy module (kept fixed in this tuning sweep).
RERANK_FLOOR = 0.60

CANDIDATES = [0.04, 0.05, 0.06, 0.065, 0.07, 0.08, 0.09, 0.10]


def load_outputs(p: Path) -> List[Dict]:
    out = []
    with p.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_split_map(p: Path) -> Dict[str, str]:
    m = {}
    with p.open() as f:
        for r in csv.DictReader(f):
            m[r["query_id"]] = r.get("split", "")
    return m


def simulate_b4_at_threshold(records: List[Dict], threshold: float) -> Dict[str, Dict]:
    """Replay the B4 surface decision per record at a new overlap threshold.

    For each record, look at the stored evidence_strength.top_rerank and
    top_overlap, plus the support_rate (from claim_verification), and
    decide whether the record would have been generated / extractive /
    abstained at this candidate threshold.

    Returns a dict {qid: new_mode_used}.
    """
    out = {}
    for r in records:
        qid = r["query_id"]
        es = r.get("evidence_strength") or {}
        top_rerank = float(es.get("top_rerank") or 0.0)
        top_overlap = float(es.get("top_overlap") or 0.0)
        original_mode = r.get("mode_used") or ""

        # If the record was originally "generative" (gate passed), it stays generative.
        # Recover support_rate from the original (pre-fallback) verification record.
        # The replay output already records the post-B4 support_rate so we use
        # the pre-fallback decision proxy: original_mode != generative AND
        # answer was INSUFFICIENT_EVIDENCE in source means the gate fired.
        if original_mode == "generative":
            out[qid] = "generative"
            continue

        # Else simulate fallback rule with the new threshold.
        if not es:
            out[qid] = "abstained"
            continue
        if top_rerank < RERANK_FLOOR:
            out[qid] = "abstained"
            continue
        if top_overlap < threshold:
            out[qid] = "abstained"
            continue
        # Otherwise: extractive_fallback (matches the policy module).
        out[qid] = "extractive_fallback"
    return out


def compute_metrics(records: List[Dict], new_modes: Dict[str, str]) -> Dict[str, float]:
    """Recompute Answer Rate / Abstention Accuracy at the new modes."""
    answerable_total = 0
    answerable_answered = 0
    unanswerable_total = 0
    unanswerable_correctly_abstained = 0
    n_surfaced = 0
    n_surfaced_unanswerable = 0

    for r in records:
        qid = r["query_id"]
        cat = r.get("category")
        mode = new_modes.get(qid, "abstained")
        is_surfaced = mode in ("generative", "extractive_fallback")
        if cat == "answerable":
            answerable_total += 1
            if is_surfaced:
                answerable_answered += 1
        elif cat == "unanswerable":
            unanswerable_total += 1
            if not is_surfaced:
                unanswerable_correctly_abstained += 1
            else:
                n_surfaced_unanswerable += 1
        if is_surfaced:
            n_surfaced += 1

    ar = answerable_answered / answerable_total if answerable_total else float("nan")
    aa = unanswerable_correctly_abstained / unanswerable_total if unanswerable_total else float("nan")
    return {
        "answer_rate": round(ar, 4),
        "abstention_accuracy": round(aa, 4),
        "n_answerable_total": answerable_total,
        "n_answerable_answered": answerable_answered,
        "n_unanswerable_total": unanswerable_total,
        "n_unanswerable_surfaced": n_surfaced_unanswerable,
        "n_surfaced_total": n_surfaced,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--b4-run", type=Path, default=DEFAULT_B4_RUN)
    parser.add_argument("--golden-set", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument(
        "--out-csv", type=Path,
        default=ROOT / "results/tables/b4_threshold_tune_dev.csv",
    )
    args = parser.parse_args()

    records = load_outputs(args.b4_run / "outputs.jsonl")
    split_map = load_split_map(args.golden_set)
    dev_records = [r for r in records if split_map.get(r["query_id"]) == "dev"]
    test_records = [r for r in records if split_map.get(r["query_id"]) == "test"]

    print(f"Loaded {len(records)} B4 records (dev={len(dev_records)}, test={len(test_records)})")
    rows = []
    for t in CANDIDATES:
        new_modes_dev = simulate_b4_at_threshold(dev_records, t)
        new_modes_test = simulate_b4_at_threshold(test_records, t)
        m_dev = compute_metrics(dev_records, new_modes_dev)
        m_test = compute_metrics(test_records, new_modes_test)
        row = {
            "candidate_threshold": t,
            "dev_answer_rate": m_dev["answer_rate"],
            "dev_abstention_accuracy": m_dev["abstention_accuracy"],
            "dev_n_unanswerable_surfaced": m_dev["n_unanswerable_surfaced"],
            "test_answer_rate_projection": m_test["answer_rate"],
            "test_abstention_accuracy_projection": m_test["abstention_accuracy"],
            "test_n_unanswerable_surfaced_projection": m_test["n_unanswerable_surfaced"],
        }
        rows.append(row)

    # Selection: largest threshold drop with dev abstention accuracy == 1.0;
    # tie-break by dev answer rate descending.
    eligible = [r for r in rows if r["dev_abstention_accuracy"] == 1.0]
    eligible.sort(key=lambda r: (-r["dev_answer_rate"], r["candidate_threshold"]))
    selected = eligible[0]["candidate_threshold"] if eligible else None

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) + ["selected"]
    with args.out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            r2 = dict(r)
            r2["selected"] = (r["candidate_threshold"] == selected)
            w.writerow(r2)

    print(f"\nCandidate sweep (dev split, n={len(dev_records)} queries):")
    print(f"  {'threshold':>10}  {'dev_AR':>8}  {'dev_AbsAcc':>11}  {'dev_unanswerable_surfaced':>26}")
    for r in rows:
        marker = "  <-- selected" if r["candidate_threshold"] == selected else ""
        print(
            f"  {r['candidate_threshold']:>10.3f}  "
            f"{r['dev_answer_rate']:>8.4f}  "
            f"{r['dev_abstention_accuracy']:>11.4f}  "
            f"{r['dev_n_unanswerable_surfaced']:>26d}"
            f"{marker}"
        )

    print(f"\nWrote {args.out_csv}")
    print(f"SELECTED THRESHOLD: {selected}")
    if selected is not None:
        # Print projected test-split metrics at the selected threshold
        new_modes_test = simulate_b4_at_threshold(test_records, selected)
        m_test = compute_metrics(test_records, new_modes_test)
        print(
            f"Projected test split @ tau={selected}: "
            f"AR={m_test['answer_rate']:.4f}, "
            f"AbsAcc={m_test['abstention_accuracy']:.4f}, "
            f"unanswerable surfaced={m_test['n_unanswerable_surfaced']}"
        )
        # Full-set projection
        new_modes_full = simulate_b4_at_threshold(records, selected)
        m_full = compute_metrics(records, new_modes_full)
        print(
            f"Projected FULL set @ tau={selected}: "
            f"AR={m_full['answer_rate']:.4f}, "
            f"AbsAcc={m_full['abstention_accuracy']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
