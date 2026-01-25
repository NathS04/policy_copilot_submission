#!/usr/bin/env python3
"""
Generates a golden set template CSV from processed paragraphs.
Suggests candidate questions from paragraph headings/keywords.
"""
import argparse
import csv
import re
from pathlib import Path


def _extract_topics(text: str) -> list[str]:
    """Heuristic: extract likely topics from paragraph text."""
    topics = []
    # headings
    for m in re.finditer(r'(?:^|\n)#+\s+(.+)', text):
        topics.append(m.group(1).strip())
    # strong keywords
    policy_keywords = [
        "must", "required", "shall", "prohibited", "allowed",
        "permitted", "mandatory", "forbidden", "policy",
    ]
    for kw in policy_keywords:
        if kw in text.lower():
            # extract the sentence containing the keyword
            for sent in re.split(r'[.!?]', text):
                if kw in sent.lower() and len(sent.strip()) > 20:
                    topics.append(sent.strip()[:80])
                    break
    return topics[:3]  # limit


def main():
    parser = argparse.ArgumentParser(
        description="Generate a golden set template from processed paragraphs."
    )
    parser.add_argument("--paragraphs", default="data/corpus/processed/paragraphs.csv",
                        help="Path to processed paragraphs CSV")
    parser.add_argument("--output", default="eval/golden_set/golden_set_template.csv",
                        help="Output template CSV path")
    parser.add_argument("--max_suggestions", type=int, default=100,
                        help="Max topic suggestions to generate")
    args = parser.parse_args()

    para_path = Path(args.paragraphs)
    if not para_path.exists():
        print(f"[!] Paragraphs file not found: {para_path}")
        print("    Run scripts/ingest_corpus.py first.")
        return

    suggestions = []
    with open(para_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text", "")
            doc_id = row.get("doc_id", "")
            para_id = row.get("paragraph_id", "")
            topics = _extract_topics(text)
            for topic in topics:
                suggestions.append({
                    "doc_id": doc_id,
                    "paragraph_id": para_id,
                    "suggested_topic": topic,
                })

    # deduplicate by topic
    seen = set()
    unique = []
    for s in suggestions:
        key = s["suggested_topic"].lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(s)

    unique = unique[:args.max_suggestions]

    # write template
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "query_id", "question", "category", "split",
            "gold_doc_ids", "gold_paragraph_ids", "notes"
        ])
        for i, s in enumerate(unique, 1):
            writer.writerow([
                f"q_{i:03d}",
                f"[WRITE QUESTION ABOUT: {s['suggested_topic']}]",
                "answerable",
                "test",
                s["doc_id"],
                s["paragraph_id"],
                f"Suggested from {s['doc_id']}",
            ])

    print(f"[✓] Template written to {out_path} ({len(unique)} suggestions)")
    print("    Edit this file to create real questions, then copy rows to golden_set.csv")


if __name__ == "__main__":
    main()
