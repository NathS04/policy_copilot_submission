"""B5 failure analysis (Phase 5 of the final round).

For each false positive (unanswerable surfaced) and false negative
(answerable abstained) in the final B5 run, dump:
  query_id, question, category, mode_used, answerability_reason,
  top retrieved paragraph id + rerank + overlap, gold paragraph ids
  (looked up at analysis time only — NOT at inference time).

Outputs:
  results/tables/b5_failure_analysis.csv
  docs/evidence/verification/b5_failure_analysis.md
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "results/runs/b5_evidence_gated_hybrid_v3_final"
DEFAULT_GOLDEN = ROOT / "eval/golden_set/golden_set_v2_corrected.csv"


def load_outputs(p: Path) -> List[Dict]:
    out = []
    with p.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_golden(p: Path) -> Dict[str, Dict]:
    rows = {}
    with p.open() as f:
        for r in csv.DictReader(f):
            rows[r["query_id"]] = r
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--golden-set", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--out-csv", type=Path,
                        default=ROOT / "results/tables/b5_failure_analysis.csv")
    parser.add_argument("--out-md", type=Path,
                        default=ROOT / "docs/evidence/verification/b5_failure_analysis.md")
    args = parser.parse_args()

    records = load_outputs(args.run_dir / "outputs.jsonl")
    golden = load_golden(args.golden_set)

    fps = []  # unanswerable surfaced
    fns = []  # answerable abstained
    for rec in records:
        cat = rec.get("category", "")
        mode = rec.get("mode_used", "")
        gold = golden.get(rec["query_id"], {})
        is_surfaced = mode != "abstained"
        if cat == "unanswerable" and is_surfaced:
            fps.append((rec, gold))
        elif cat == "answerable" and not is_surfaced:
            fns.append((rec, gold))

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "kind", "query_id", "question", "category",
        "mode_used", "answerability_reason",
        "top_rerank", "top_overlap", "qualifier_in_top",
        "top_paragraph_id", "gold_paragraph_ids",
    ]
    with args.out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for kind, rows in (("false_positive", fps), ("false_negative", fns)):
            for rec, gold in rows:
                es = rec.get("evidence_strength") or {}
                top_ev = (rec.get("evidence") or [{}])[0]
                w.writerow({
                    "kind": kind,
                    "query_id": rec.get("query_id"),
                    "question": rec.get("question", ""),
                    "category": rec.get("category"),
                    "mode_used": rec.get("mode_used"),
                    "answerability_reason": rec.get("answerability_reason", ""),
                    "top_rerank": es.get("top_rerank"),
                    "top_overlap": es.get("top_overlap"),
                    "qualifier_in_top": es.get("qualifier_in_top"),
                    "top_paragraph_id": top_ev.get("paragraph_id", ""),
                    "gold_paragraph_ids": gold.get("gold_paragraph_ids", ""),
                })

    # Markdown summary
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    with args.out_md.open("w") as f:
        f.write("# B5 Evidence-Gated Hybrid — Failure Analysis\n\n")
        f.write(
            "This document enumerates every false positive "
            "(unanswerable surfaced) and false negative (answerable abstained) "
            "from `results/runs/b5_evidence_gated_hybrid_v3_final/outputs.jsonl`. "
            "It is produced by `scripts/analyse_b5_failures.py` against "
            "`eval/golden_set/golden_set_v2_corrected.csv`. Gold paragraph "
            "IDs are looked up at analysis time only; they are not used "
            "at inference time by the B5 gate.\n\n"
        )
        f.write(f"- False positives (unanswerable surfaced): **{len(fps)}**\n")
        f.write(f"- False negatives (answerable abstained):  **{len(fns)}**\n\n")
        f.write("## False positives — unanswerable queries B5 still surfaces\n\n")
        if not fps:
            f.write("_None._\n\n")
        for rec, gold in fps:
            es = rec.get("evidence_strength") or {}
            top_ev = (rec.get("evidence") or [{}])[0]
            f.write(f"### `{rec.get('query_id')}` — \"{rec.get('question','')}\"\n\n")
            f.write(f"- mode_used: `{rec.get('mode_used')}`\n")
            f.write(f"- answerability_reason: `{rec.get('answerability_reason','')}`\n")
            f.write(
                f"- top_rerank: `{es.get('top_rerank')}`, "
                f"top_overlap: `{es.get('top_overlap')}`, "
                f"qualifier_in_top: `{es.get('qualifier_in_top')}`\n"
            )
            f.write(f"- top paragraph: `{top_ev.get('paragraph_id','')}`\n")
            text_snip = (top_ev.get("text") or "").strip().replace("\n", " ")[:300]
            f.write(f"- top text snippet: \"{text_snip}…\"\n\n")
        f.write("## False negatives — answerable queries B5 abstains on\n\n")
        if not fns:
            f.write("_None._\n\n")
        for rec, gold in fns:
            es = rec.get("evidence_strength") or {}
            top_ev = (rec.get("evidence") or [{}])[0]
            f.write(f"### `{rec.get('query_id')}` — \"{rec.get('question','')}\"\n\n")
            f.write(f"- mode_used: `{rec.get('mode_used')}`\n")
            f.write(f"- answerability_reason: `{rec.get('answerability_reason','')}`\n")
            f.write(
                f"- top_rerank: `{es.get('top_rerank')}`, "
                f"top_overlap: `{es.get('top_overlap')}`, "
                f"qualifier_in_top: `{es.get('qualifier_in_top')}`\n"
            )
            f.write(f"- top paragraph: `{top_ev.get('paragraph_id','')}`\n")
            f.write("- gold paragraph IDs (from golden set, not used at inference):\n")
            gids = (gold.get("gold_paragraph_ids") or "").split(",")
            for g in gids[:3]:
                f.write(f"    - `{g.strip()}`\n")
            f.write("\n")

    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    print(f"\nFalse positives:  {len(fps)} (target ≤ 2 for AbsAcc ≥ 80% on n=13)")
    print(f"False negatives: {len(fns)} (target ≤ 8 for AR ≥ 80% on n=40)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
