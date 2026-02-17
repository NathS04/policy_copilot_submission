#!/usr/bin/env python3
"""
Export an annotation pack for human evaluation.
Reads a run's outputs.jsonl and creates a JSONL pack with empty score fields.
"""
import argparse
import json
import random
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Export human evaluation annotation pack."
    )
    parser.add_argument("--run_name", required=True,
                        help="Name of the run (reads results/runs/<run_name>/outputs.jsonl)")
    parser.add_argument("--split", choices=["dev", "test"], default="test",
                        help="Golden set split to include")
    parser.add_argument("--n", type=int, default=20,
                        help="Number of items to include in pack")
    parser.add_argument("--golden_set", default="eval/golden_set/golden_set.csv",
                        help="Path to golden_set.csv for split filtering")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for sampling")
    parser.add_argument("--rater", default=None,
                        help="Optional rater name (adds suffix to filename)")
    args = parser.parse_args()

    run_dir = Path("results/runs") / args.run_name
    outputs_path = run_dir / "outputs.jsonl"

    if not outputs_path.exists():
        print(f"[!] outputs.jsonl not found at {outputs_path}")
        sys.exit(1)

    # load golden set splits
    import csv
    split_ids = set()
    gs_path = Path(args.golden_set)
    if gs_path.exists():
        with open(gs_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("split") == args.split:
                    split_ids.add(row.get("query_id", ""))

    # load outputs
    records = []
    with open(outputs_path, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                qid = obj.get("query_id", "")
                if split_ids and qid not in split_ids:
                    continue
                records.append(obj)
            except json.JSONDecodeError:
                continue

    if not records:
        print(f"[!] No records found for split '{args.split}'")
        sys.exit(1)

    # sample
    random.seed(args.seed)
    if len(records) > args.n:
        records = random.sample(records, args.n)

    # build annotation pack
    pack = []
    for r in records:
        # get evidence snippets
        evidence_snippets = []
        if "evidence" in r:
            for e in r.get("evidence", []):
                evidence_snippets.append({
                    "paragraph_id": e.get("paragraph_id", ""),
                    "text": e.get("text", "")[:300],
                })
        item = {
            "query_id": r.get("query_id", ""),
            "question": r.get("question", ""),
            "answer": r.get("answer", ""),
            "citations": r.get("citations", []),
            "evidence_snippets": evidence_snippets,
            "baseline": r.get("baseline", ""),
            "category": r.get("category", ""),
            # empty score fields for annotator to fill
            "scores": {
                "G0_ungrounded_present": None,  # true/false
                "G1_support_ratio": None,        # 0.0-1.0
                "G2_citation_correctness": None, # 0, 1, or 2
                "U1_answer_clarity": None,       # 1-5
                "U2_actionability": None,        # 1-5
                "comments": "",
            }
        }
        pack.append(item)

    # write pack
    packs_dir = Path("eval/human_eval/packs")
    packs_dir.mkdir(parents=True, exist_ok=True)

    suffix = f"_{args.rater}" if args.rater else ""
    pack_filename = f"{args.run_name}_{args.split}_pack{suffix}.jsonl"
    pack_path = packs_dir / pack_filename

    with open(pack_path, "w") as f:
        for item in pack:
            f.write(json.dumps(item) + "\n")

    print(f"[✓] Exported {len(pack)} items to {pack_path}")
    print("    Fill the 'scores' fields and then import with:")
    print(f"    python scripts/import_human_eval_pack.py --run_name {args.run_name} --pack {pack_path}")


if __name__ == "__main__":
    main()
