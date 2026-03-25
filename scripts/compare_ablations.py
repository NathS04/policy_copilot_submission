#!/usr/bin/env python3
"""Compare ablation runs side-by-side with metric deltas.

Loads summary.json from the full B3 pipeline and each ablation variant,
producing a comparison table showing which components contribute most.
Output: results/tables/ablation_comparison.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

RUNS_DIR = Path(__file__).resolve().parent.parent / "results" / "runs"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results" / "tables"

COMPARISON_METRICS = [
    "answer_rate",
    "abstention_accuracy",
    "evidence_recall_at_5",
    "evidence_precision_at_5",
    "citation_precision",
    "citation_recall",
    "ungrounded_rate",
    "support_rate_mean",
    "contradiction_recall",
    "contradiction_precision",
]


def load_summary(run_name: str) -> dict | None:
    """Load summary.json for a run."""
    path = RUNS_DIR / run_name / "summary.json"
    if not path.exists():
        logger.warning("summary.json not found for %s", run_name)
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _safe_float(val) -> float | None:
    """Convert a metric value to float, returning None for N/A."""
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def compare_runs(
    base_name: str, base_summary: dict,
    ablation_name: str, ablation_summary: dict,
) -> dict:
    """Compare a single ablation against the base run."""
    row = {"ablation": ablation_name, "base_run": base_name}

    for metric in COMPARISON_METRICS:
        base_val = _safe_float(base_summary.get("metrics", base_summary).get(metric))
        abl_val = _safe_float(ablation_summary.get("metrics", ablation_summary).get(metric))

        row[f"{metric}_base"] = f"{base_val:.4f}" if base_val is not None else "N/A"
        row[f"{metric}_ablation"] = f"{abl_val:.4f}" if abl_val is not None else "N/A"

        if base_val is not None and abl_val is not None:
            delta = abl_val - base_val
            row[f"{metric}_delta"] = f"{delta:+.4f}"
        else:
            row[f"{metric}_delta"] = "N/A"

    return row


def find_ablation_runs() -> list[str]:
    """Find all runs that look like B3 ablations."""
    ablations = []
    if not RUNS_DIR.exists():
        return ablations
    for d in sorted(RUNS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        config_path = d / "run_config.json"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
            abl = cfg.get("ablations", {})
            if any(abl.values()):
                ablations.append(d.name)
    return ablations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base", default="b3_generative_bm25_fallback_final",
        help="Base B3 run name",
    )
    parser.add_argument(
        "--ablations", nargs="*", default=None,
        help="Ablation run names (auto-detected if omitted)",
    )
    parser.add_argument(
        "--include-baselines", action="store_true",
        help="Also compare B1 and B2 against B3",
    )
    parser.add_argument(
        "--output", type=Path,
        default=OUTPUT_DIR / "ablation_comparison.csv",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    base_summary = load_summary(args.base)
    if not base_summary:
        logger.error("Base run %s not found.", args.base)
        sys.exit(1)

    ablation_names = args.ablations or find_ablation_runs()

    if args.include_baselines:
        for bn in ["b1_generative_final", "b2_generative_bm25_fallback_final"]:
            if bn not in ablation_names and bn != args.base:
                ablation_names.insert(0, bn)

    if not ablation_names:
        logger.info("No ablation runs found. Comparing baselines only.")
        ablation_names = ["b1_generative_final", "b2_generative_bm25_fallback_final"]

    rows = []
    for abl_name in ablation_names:
        abl_summary = load_summary(abl_name)
        if abl_summary:
            row = compare_runs(args.base, base_summary, abl_name, abl_summary)
            rows.append(row)
            logger.info("Compared %s vs %s", args.base, abl_name)

    if not rows:
        logger.error("No comparisons produced.")
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["ablation", "base_run"]
    for metric in COMPARISON_METRICS:
        fieldnames.extend([
            f"{metric}_base", f"{metric}_ablation", f"{metric}_delta",
        ])

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    logger.info("Wrote %s (%d comparisons)", args.output, len(rows))


if __name__ == "__main__":
    main()
