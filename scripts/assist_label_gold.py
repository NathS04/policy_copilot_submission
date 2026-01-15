#!/usr/bin/env python3
"""
Interactive CLI to assist labelling gold_paragraph_ids for golden set queries.
Shows top-k retrieval results and lets the user select correct paragraph IDs.
"""
import argparse
import csv
import sys
from pathlib import Path

from policy_copilot.config import settings


def _load_golden_set(path: str) -> list[dict]:
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _save_golden_set(path: str, rows: list[dict]):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Assist labelling gold paragraph IDs for golden set queries."
    )
    parser.add_argument("--query_id", required=True,
                        help="Query ID to label (e.g., q_012)")
    parser.add_argument("--golden_set", default=settings.GOLDEN_SET_PATH,
                        help="Path to golden_set.csv")
    parser.add_argument("--top_k", type=int, default=10,
                        help="Number of retrieval results to show")
    args = parser.parse_args()

    # load golden set
    golden_path = Path(args.golden_set)
    if not golden_path.exists():
        print(f"[!] Golden set not found: {golden_path}")
        sys.exit(1)

    rows = _load_golden_set(args.golden_set)
    target_row = None
    target_idx = None
    for i, r in enumerate(rows):
        if r.get("query_id") == args.query_id:
            target_row = r
            target_idx = i
            break

    if target_row is None:
        print(f"[!] Query ID '{args.query_id}' not found in golden set.")
        sys.exit(1)

    question = target_row.get("question", "")
    category = target_row.get("category", "")
    current_gold = target_row.get("gold_paragraph_ids", "")

    print(f"\n{'='*60}")
    print(f"Query ID:  {args.query_id}")
    print(f"Question:  {question}")
    print(f"Category:  {category}")
    print(f"Current gold IDs: {current_gold or '(empty)'}")
    print(f"{'='*60}\n")

    # try to load retriever
    try:
        from policy_copilot.retrieve.retriever import Retriever
        retriever = Retriever()
        if not retriever.loaded:
            print("[!] FAISS index not loaded. Showing no results.")
            print("    Run: python scripts/build_index.py")
            retriever = None
    except Exception as e:
        print(f"[!] Could not load retriever: {e}")
        retriever = None

    if retriever:
        results = retriever.retrieve(question, k=args.top_k)
        print(f"Top-{args.top_k} retrieval results:\n")
        for i, r in enumerate(results, 1):
            pid = r.get("paragraph_id", "?")
            doc = r.get("doc_id", "?")
            page = r.get("page", "?")
            text = r.get("text", "")[:120]
            score = r.get("score", 0.0)
            print(f"  [{i}] {pid}")
            print(f"      doc={doc}  page={page}  score={score:.4f}")
            print(f"      {text}...")
            print()

    # ask user for gold IDs
    print("Enter gold paragraph_ids (comma-separated), or 'skip' to skip:")
    print("  Example: doc_handbook_v1::p0002::i0000::abc123,doc_handbook_v1::p0003::i0001::def456")
    user_input = input("> ").strip()

    if user_input.lower() == "skip":
        print("[–] Skipped.")
        return

    # update the row
    gold_ids = user_input.strip()
    rows[target_idx]["gold_paragraph_ids"] = gold_ids

    # also set doc IDs from the paragraph IDs
    doc_ids = set()
    for pid in gold_ids.split(","):
        parts = pid.strip().split("::")
        if parts:
            doc_ids.add(parts[0])
    if doc_ids:
        rows[target_idx]["gold_doc_ids"] = ",".join(sorted(doc_ids))

    _save_golden_set(args.golden_set, rows)
    print(f"[✓] Updated {args.query_id} with gold_paragraph_ids: {gold_ids}")
    print(f"    Saved to {args.golden_set}")


if __name__ == "__main__":
    main()
