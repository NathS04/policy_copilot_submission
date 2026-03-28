#!/usr/bin/env python3
"""Evaluate the objective-slice subset of the golden set.

The objective slice contains queries whose answers are deterministically
checkable (specific numbers, yes/no, named procedures) without LLM
judgement. This script filters predictions to that subset and reports
answer rate, abstention rate, and retrieval recall.

Usage:
    python scripts/eval_objective_slice.py [--run RUN_NAME]
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
GOLDEN_SET = BASE / "eval" / "golden_set" / "golden_set.csv"
RUNS_DIR = BASE / "results" / "runs"


def load_objective_ids() -> set[str]:
    """Load query IDs tagged as objective_slice=true."""
    ids: set[str] = set()
    if not GOLDEN_SET.exists():
        logger.error("Golden set not found: %s", GOLDEN_SET)
        return ids
    with open(GOLDEN_SET, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("objective_slice", "").strip().lower() == "true":
                ids.add(row["query_id"].strip())
    return ids


def evaluate_run(run_name: str, objective_ids: set[str]) -> dict:
    """Evaluate a single run on the objective slice."""
    pred_path = RUNS_DIR / run_name / "predictions.csv"
    if not pred_path.exists():
        logger.error("predictions.csv not found for %s", run_name)
        return {}

    total = 0
    answered = 0
    abstained = 0
    non_answers = {"INSUFFICIENT_EVIDENCE", "LLM_DISABLED", "ERROR", ""}

    with open(pred_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            qid = row.get("query_id", "").strip()
            if qid not in objective_ids:
                continue
            total += 1
            answer = row.get("answer", "").strip()
            is_abs = row.get("is_abstained", "").strip().lower() in ("true", "1")

            if is_abs or answer in non_answers:
                abstained += 1
            else:
                answered += 1

    if total == 0:
        return {"run": run_name, "objective_queries": 0}

    return {
        "run": run_name,
        "objective_queries": total,
        "answered": answered,
        "abstained": abstained,
        "answer_rate": round(answered / total, 4),
        "abstention_rate": round(abstained / total, 4),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", nargs="*",
        default=[
            "b1_generative_final",
            "b2_generative_bm25_fallback_final",
            "b3_generative_bm25_fallback_final",
        ],
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    objective_ids = load_objective_ids()
    if not objective_ids:
        logger.error("No objective-slice queries found in golden set.")
        sys.exit(1)

    logger.info("Objective slice: %d queries", len(objective_ids))

    for run_name in args.run:
        result = evaluate_run(run_name, objective_ids)
        if result:
            logger.info(
                "%s: %d objective queries, %d answered (%.0f%%), %d abstained (%.0f%%)",
                result["run"],
                result.get("objective_queries", 0),
                result.get("answered", 0),
                result.get("answer_rate", 0) * 100,
                result.get("abstained", 0),
                result.get("abstention_rate", 0) * 100,
            )

    output_path = BASE / "results" / "tables" / "objective_slice_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for run_name in args.run:
        r = evaluate_run(run_name, objective_ids)
        if r:
            results.append(r)

    if results:
        fieldnames = ["run", "objective_queries", "answered", "abstained", "answer_rate", "abstention_rate"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow({k: r.get(k, "") for k in fieldnames})
        logger.info("Wrote %s", output_path)


if __name__ == "__main__":
    main()
