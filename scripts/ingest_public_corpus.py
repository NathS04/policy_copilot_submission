"""Ingest the downloaded public guidance .txt files into the same
paragraphs.jsonl format the synthetic corpus uses, so the existing
retrieval and abstention pipeline can run against it unchanged.

Reads:  data/public_transfer_corpus/raw/*.txt
Writes: data/public_transfer_corpus/processed/paragraphs.jsonl

Each paragraph row carries the same schema the synthetic corpus uses
(see data/corpus/processed/paragraphs.jsonl):

    doc_id, source_file, page, paragraph_index,
    paragraph_id, text, char_len

There is no real "page" concept in HTML, so all paragraphs land on
page 1 to keep the schema and ID format unchanged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from policy_copilot.ingest.chunking import chunk_text_to_paragraphs  # noqa: E402
from policy_copilot.ingest.paragraph_ids import generate_paragraph_id  # noqa: E402


RAW_DIR = HERE / "data" / "public_transfer_corpus" / "raw"
OUT_PATH = HERE / "data" / "public_transfer_corpus" / "processed" / "paragraphs.jsonl"


def main() -> int:
    if not RAW_DIR.exists():
        raise SystemExit(f"Missing {RAW_DIR}; run scripts/download_public_corpus.py first")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for txt_path in sorted(RAW_DIR.glob("*.txt")):
        doc_id = txt_path.stem
        text = txt_path.read_text(encoding="utf-8")
        paragraphs = chunk_text_to_paragraphs(text)
        for idx, p in enumerate(paragraphs):
            pid = generate_paragraph_id(doc_id, page=1, para_index=idx, content=p)
            rows.append({
                "doc_id": doc_id,
                "source_file": txt_path.name,
                "page": 1,
                "paragraph_index": idx,
                "paragraph_id": pid,
                "text": p,
                "char_len": len(p),
            })
        print(f"  {doc_id}: {len(paragraphs)} paragraphs")

    with OUT_PATH.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nWrote {OUT_PATH} ({len(rows)} paragraphs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
