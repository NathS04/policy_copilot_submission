"""Run reproducible component ablations (Phase G).

Runs five B3-Extractive configurations on the corrected golden set
(``golden_set_v2_corrected.csv``) with the hybrid backend:

  1. Full B3 (reference; reuses existing b3_extractive_hybrid_v2_final)
  2. minus reranker         (--no_rerank)
  3. minus verification     (--no_verify)
  4. minus abstention gate  (--abstain_threshold 0.0 --min_support_rate 0.0)
  5. minus contradictions   (--no_contradictions)

Each ablation is a real, reproducible run with its own
run_config.json + outputs.jsonl + summary.json. The aggregated table
goes to results/tables/component_ablation_final.csv.

Generative ablations require an API key and are intentionally NOT run
here — they can be added in Phase K if a key is supplied.

No LLM calls (extractive mode).
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "eval/golden_set/golden_set_v2_corrected.csv"
BACKEND = "hybrid"

ABLATIONS = [
    # (run_name, extra_args, label, component_disabled)
    ("ablation_full_hybrid_v2",         [],                                          "Full B3",          "none"),
    ("ablation_no_rerank_hybrid_v2",    ["--no_rerank"],                              "minus Reranker",   "rerank"),
    ("ablation_no_verify_hybrid_v2",    ["--no_verify"],                              "minus Verification", "verify"),
    ("ablation_no_abstain_hybrid_v2",   ["--abstain_threshold", "0.0", "--min_support_rate", "0.0"], "minus Abstention Gate", "abstention"),
    ("ablation_no_contra_hybrid_v2",    ["--no_contradictions"],                      "minus Contradiction Detection", "contradiction"),
]


def run_one(run_name: str, extra_args: List[str]) -> dict:
    args = [
        sys.executable, str(ROOT / "scripts/run_eval.py"),
        "--baseline", "b3",
        "--split", "all",
        "--mode", "extractive",
        "--backend", BACKEND,
        "--golden_set", str(GOLDEN),
        "--run_name", run_name,
        "--force",
    ] + extra_args
    print(f"  running {run_name} args={extra_args}")
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(
            f"ablation {run_name} failed:\n{proc.stdout[-800:]}\n{proc.stderr[-800:]}"
        )
    summary = json.loads((ROOT / "results/runs" / run_name / "summary.json").read_text())
    return summary


def write_ablation_table(rows: list[dict], out_path: Path) -> None:
    fields = [
        "run_name", "label", "component_disabled",
        "answer_rate", "abstention_accuracy", "evidence_recall_at_5",
        "evidence_mrr", "citation_precision", "citation_recall",
        "ungrounded_rate", "support_rate_mean",
        "contradiction_recall", "contradiction_precision",
        "total_queries", "source",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-csv", type=Path,
                        default=ROOT / "results/tables/component_ablation_final.csv")
    args = parser.parse_args()

    rows = []
    for run_name, extra_args, label, component in ABLATIONS:
        summary = run_one(run_name, extra_args)
        summary["run_name"] = run_name
        summary["label"] = label
        summary["component_disabled"] = component
        summary["source"] = "reproducible_extractive_hybrid_v2_corrected"
        rows.append(summary)

    write_ablation_table(rows, args.out_csv)

    print("\n=== Ablation summary ===")
    for r in rows:
        print(
            f"  {r['label']:>30}: "
            f"AR={r.get('answer_rate', '-'):>6} "
            f"AbsAcc={r.get('abstention_accuracy', '-'):>6} "
            f"Rec@5={r.get('evidence_recall_at_5', '-'):>6} "
            f"Ung={r.get('ungrounded_rate', '-'):>6}"
        )
    print(f"\nWrote {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
