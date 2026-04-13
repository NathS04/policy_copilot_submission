#!/usr/bin/env python3
"""Classify evaluation errors into the failure-mode taxonomy.

Reads predictions.csv from each shipped run and classifies each query
into diagnostic categories defined in eval/analysis/error_taxonomy.md.
Outputs results/tables/failure_taxonomy.csv with per-baseline counts.
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

FINAL_RUNS = [
    "b1_generative_final",
    "b2_generative_bm25_fallback_final",
    "b3_generative_bm25_fallback_final",
]

TAXONOMY = [
    "missed_retrieval",
    "chunk_boundary",
    "wrong_claim_evidence_link",
    "unsupported_generation",
    "contradiction_ignored",
    "abstention_error",
    "format_error",
]


def _parse_list(val: str) -> list[str]:
    """Parse a CSV cell that may contain a JSON list or semicolon-separated IDs."""
    if not val or val.strip() in ("", "[]", "None"):
        return []
    val = val.strip()
    if val.startswith("["):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            pass
    return [v.strip() for v in val.split(";") if v.strip()]


def _load_golden_set() -> dict[str, list[str]]:
    """Load golden set and return {query_id: [gold_paragraph_ids]}."""
    gs_path = Path(__file__).resolve().parent.parent / "eval" / "golden_set" / "golden_set.csv"
    mapping: dict[str, list[str]] = {}
    if not gs_path.exists():
        return mapping
    with open(gs_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            qid = row.get("query_id", "").strip()
            gold = _parse_list(row.get("gold_paragraph_ids", ""))
            if qid:
                mapping[qid] = gold
    return mapping


_GOLD_IDS: dict[str, list[str]] | None = None


def _get_gold_ids() -> dict[str, list[str]]:
    global _GOLD_IDS
    if _GOLD_IDS is None:
        _GOLD_IDS = _load_golden_set()
    return _GOLD_IDS


def classify_row(row: dict) -> list[str]:
    """Return list of taxonomy categories that apply to this prediction row."""
    cats: list[str] = []
    category = row.get("category", "").strip().lower()
    is_abstained = row.get("is_abstained", "").strip().lower() in ("true", "1", "yes")
    answer = row.get("answer", "").strip()
    error = row.get("error", "").strip()
    retrieved = _parse_list(row.get("retrieved_ids_topk", ""))
    citations = _parse_list(row.get("citations", ""))
    unsupported = row.get("unsupported_claims", "").strip()
    contradictions = row.get("contradictions_found", "").strip()

    if error:
        cats.append("format_error")
        return cats

    no_answer = is_abstained or not answer or answer in (
        "INSUFFICIENT_EVIDENCE", "LLM_DISABLED", "ERROR"
    )

    gold_ids = _get_gold_ids()
    qid = row.get("query_id", "").strip()
    gold_pids = set(gold_ids.get(qid, []))

    if category == "answerable":
        if no_answer:
            cats.append("abstention_error")
        if not retrieved:
            cats.append("missed_retrieval")
        elif gold_pids and retrieved:
            retr_set = set(retrieved)
            overlap = gold_pids & retr_set
            if not overlap:
                cats.append("missed_retrieval")
            elif overlap and overlap != gold_pids:
                cats.append("chunk_boundary")
        if unsupported and unsupported not in ("0", ""):
            try:
                if int(unsupported) > 0:
                    cats.append("unsupported_generation")
            except ValueError:
                pass
        if citations and retrieved:
            cite_set = set(_parse_list(row.get("citations", "")))
            retr_set = set(retrieved)
            if cite_set and not cite_set.issubset(retr_set):
                cats.append("wrong_claim_evidence_link")

    elif category == "unanswerable":
        if not no_answer:
            cats.append("unsupported_generation")
            cats.append("abstention_error")

    elif category == "contradiction":
        if not contradictions or contradictions in ("0", "[]", ""):
            cats.append("contradiction_ignored")
        try:
            if int(contradictions) == 0:
                if "contradiction_ignored" not in cats:
                    cats.append("contradiction_ignored")
        except ValueError:
            pass

    return cats


def process_run(run_name: str) -> dict[str, int]:
    """Process a single run directory and return taxonomy counts."""
    pred_path = RUNS_DIR / run_name / "predictions.csv"
    if not pred_path.exists():
        logger.warning("predictions.csv not found for run %s", run_name)
        return {}

    counts: dict[str, int] = {cat: 0 for cat in TAXONOMY}
    total = 0

    with open(pred_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            for cat in classify_row(row):
                counts[cat] = counts.get(cat, 0) + 1

    counts["total_queries"] = total
    counts["clean_queries"] = total - sum(
        1 for row_cats in _iter_row_cats(pred_path) if row_cats
    )
    return counts


def _iter_row_cats(pred_path: Path):
    """Yield category lists for each row (used for clean count)."""
    with open(pred_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield classify_row(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs", nargs="*", default=FINAL_RUNS,
        help="Run names to classify (default: final runs)",
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_DIR / "failure_taxonomy.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    rows = []
    for run_name in args.runs:
        counts = process_run(run_name)
        if counts:
            rows.append({"run": run_name, **counts})
            logger.info(
                "%s: %d queries, %d with errors",
                run_name, counts.get("total_queries", 0),
                counts.get("total_queries", 0) - counts.get("clean_queries", 0),
            )

    if not rows:
        logger.error("No runs processed.")
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["run", "total_queries", "clean_queries"] + TAXONOMY
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, 0) for k in fieldnames})

    logger.info("Wrote %s", args.output)


if __name__ == "__main__":
    main()
