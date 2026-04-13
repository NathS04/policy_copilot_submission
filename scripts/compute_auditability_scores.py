#!/usr/bin/env python3
"""Compute auditability rubric scores from shipped evaluation runs.

Reads summary.json from each run and combines with failure-taxonomy
counts to produce a 5-axis auditability profile per baseline.
Output: results/tables/auditability_scores.csv
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
TABLES_DIR = Path(__file__).resolve().parent.parent / "results" / "tables"

FINAL_RUNS = [
    "b1_generative_final",
    "b2_generative_bm25_fallback_final",
    "b3_generative_bm25_fallback_final",
]

AXES = [
    "evidence_precision_at_5",
    "evidence_recall_at_5",
    "evidence_mrr",
    "citation_precision",
    "citation_recall",
    "abstention_accuracy",
    "false_abstention_rate",
    "contradiction_recall",
    "contradiction_precision",
    "ungrounded_rate",
    "support_rate_mean",
    "answer_rate",
    "clean_query_pct",
    "dominant_failure_mode",
]


def load_summary(run_name: str) -> dict:
    """Load summary.json for a run."""
    path = RUNS_DIR / run_name / "summary.json"
    if not path.exists():
        logger.warning("summary.json not found for %s", run_name)
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_taxonomy(run_name: str) -> dict:
    """Load failure taxonomy counts for a run from the CSV."""
    tax_path = TABLES_DIR / "failure_taxonomy.csv"
    if not tax_path.exists():
        return {}
    with open(tax_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["run"] == run_name:
                return row
    return {}


def compute_scores(run_name: str) -> dict:
    """Compute auditability scores for a single run."""
    summary = load_summary(run_name)
    taxonomy = load_taxonomy(run_name)

    if not summary:
        return {}

    metrics = summary.get("metrics", summary)

    total = int(taxonomy.get("total_queries", 0)) if taxonomy else 0
    clean = int(taxonomy.get("clean_queries", 0)) if taxonomy else 0

    failure_counts = {}
    for cat in [
        "missed_retrieval", "chunk_boundary", "wrong_claim_evidence_link",
        "unsupported_generation", "contradiction_ignored",
        "abstention_error", "format_error",
    ]:
        failure_counts[cat] = int(taxonomy.get(cat, 0))

    dominant = max(failure_counts, key=failure_counts.get) if failure_counts else "N/A"
    if failure_counts.get(dominant, 0) == 0:
        dominant = "none"

    def _get(key: str):
        val = metrics.get(key)
        if val is None:
            return ""
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    false_abstention = ""
    if "answer_rate" in metrics:
        try:
            ar = float(metrics["answer_rate"])
            false_abstention = f"{1.0 - ar:.4f}"
        except (ValueError, TypeError):
            pass

    return {
        "run": run_name,
        "evidence_precision_at_5": _get("evidence_precision_at_5"),
        "evidence_recall_at_5": _get("evidence_recall_at_5"),
        "evidence_mrr": _get("evidence_mrr"),
        "citation_precision": _get("citation_precision"),
        "citation_recall": _get("citation_recall"),
        "abstention_accuracy": _get("abstention_accuracy"),
        "false_abstention_rate": false_abstention,
        "contradiction_recall": _get("contradiction_recall"),
        "contradiction_precision": _get("contradiction_precision"),
        "ungrounded_rate": _get("ungrounded_rate"),
        "support_rate_mean": _get("support_rate_mean"),
        "answer_rate": _get("answer_rate"),
        "clean_query_pct": f"{clean / total:.4f}" if total > 0 else "",
        "dominant_failure_mode": dominant,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs", nargs="*", default=FINAL_RUNS,
        help="Run names to score",
    )
    parser.add_argument(
        "--output", type=Path,
        default=TABLES_DIR / "auditability_scores.csv",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    rows = []
    for run_name in args.runs:
        scores = compute_scores(run_name)
        if scores:
            rows.append(scores)
            logger.info("%s: dominant failure = %s", run_name, scores["dominant_failure_mode"])

    if not rows:
        logger.error("No runs processed.")
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["run"] + AXES
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    logger.info("Wrote %s", args.output)


if __name__ == "__main__":
    main()
