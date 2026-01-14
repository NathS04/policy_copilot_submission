#!/usr/bin/env python3
"""
Validates the golden set CSV for structural correctness.
Exits non-zero if any check fails.
"""
import argparse
import csv
import sys
from pathlib import Path

VALID_CATEGORIES = {"answerable", "unanswerable", "contradiction"}
VALID_SPLITS = {"train", "dev", "test"}


def validate(golden_path: str, docstore_path: str | None = None) -> list[str]:
    """Returns list of error messages. Empty = valid."""
    errors = []
    path = Path(golden_path)

    if not path.exists():
        return [f"File not found: {golden_path}"]

    with open(path, "r") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # check required columns
        required = {"query_id", "question", "category", "split",
                     "gold_doc_ids", "gold_paragraph_ids"}
        missing = required - set(headers)
        if missing:
            errors.append(f"Missing columns: {missing}")
            return errors

        rows = list(reader)

    if not rows:
        errors.append("Golden set is empty")
        return errors

    # load docstore if available
    known_pids = set()
    if docstore_path and Path(docstore_path).exists():
        import json
        with open(docstore_path, "r") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    # Handle FAISS wrapper format: {"faiss_id": ..., "meta": {"paragraph_id": ...}}
                    if "meta" in obj and isinstance(obj["meta"], dict):
                        known_pids.add(obj["meta"].get("paragraph_id", ""))
                    else:
                        known_pids.add(obj.get("paragraph_id", ""))
                except json.JSONDecodeError:
                    pass

    seen_ids = set()
    category_counts = {"answerable": 0, "unanswerable": 0, "contradiction": 0}

    for i, row in enumerate(rows, 2):  # 2 because row 1 is header
        qid = row.get("query_id", "").strip()
        question = row.get("question", "").strip()
        category = row.get("category", "").strip()
        split = row.get("split", "").strip()
        gold_pids_str = row.get("gold_paragraph_ids", "").strip()

        # unique query_id
        if not qid:
            errors.append(f"Row {i}: empty query_id")
        elif qid in seen_ids:
            errors.append(f"Row {i}: duplicate query_id '{qid}'")
        seen_ids.add(qid)

        # question not empty
        if not question:
            errors.append(f"Row {i} ({qid}): empty question")

        # valid category
        if category not in VALID_CATEGORIES:
            errors.append(f"Row {i} ({qid}): invalid category '{category}'. Must be one of {VALID_CATEGORIES}")
        else:
            category_counts[category] += 1

        # valid split
        if split not in VALID_SPLITS:
            errors.append(f"Row {i} ({qid}): invalid split '{split}'. Must be one of {VALID_SPLITS}")

        # gold paragraph ID rules
        gold_pids = [p.strip() for p in gold_pids_str.split(",") if p.strip()] if gold_pids_str else []

        if category == "answerable" and not gold_pids:
            errors.append(f"Row {i} ({qid}): answerable query must have gold_paragraph_ids")

        if category == "contradiction" and len(gold_pids) < 2:
            errors.append(f"Row {i} ({qid}): contradiction query must have ≥2 gold_paragraph_ids")

        if category == "unanswerable" and gold_pids:
            errors.append(f"Row {i} ({qid}): unanswerable query must have empty gold_paragraph_ids")

        # check paragraph IDs exist in docstore
        if known_pids and gold_pids:
            for pid in gold_pids:
                if pid and pid not in known_pids:
                    errors.append(f"Row {i} ({qid}): gold_paragraph_id '{pid}' not found in docstore")

    # summary checks
    print("\nGolden set summary:")
    print(f"  Total queries:    {len(rows)}")
    for cat, count in category_counts.items():
        print(f"  {cat:15s}: {count}")

    if len(rows) < 60:
        errors.append(f"Golden set has only {len(rows)} queries (minimum 60 required)")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate golden set CSV.")
    parser.add_argument("--golden_set",
                        default="eval/golden_set/golden_set.csv",
                        help="Path to golden_set.csv")
    parser.add_argument("--docstore",
                        default="data/corpus/processed/index/docstore.jsonl",
                        help="Path to docstore for paragraph ID validation")
    args = parser.parse_args()

    errors = validate(args.golden_set, args.docstore)

    if errors:
        print(f"\n[✗] Validation FAILED with {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n[✓] Golden set is valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()
