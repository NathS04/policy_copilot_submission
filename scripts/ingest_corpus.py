import argparse
import json
import csv
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from tqdm import tqdm

from policy_copilot.logging_utils import setup_logging
from policy_copilot.ingest.pdf_extract import extract_text_from_pdf
from policy_copilot.ingest.chunking import chunk_text_to_paragraphs
from policy_copilot.ingest.paragraph_ids import generate_paragraph_id

logger = setup_logging()

def get_file_sha256(filepath: Path) -> str:
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def ensure_manifest(manifest_path: Path):
    if not manifest_path.exists():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["doc_id", "source_file", "sha256", "pages", "added_utc", "notes", "license_ok"])

def update_manifest(manifest_path: Path, doc_info: dict):
    # Read existing to check if we need to update or append
    rows = []
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    
    # Check if doc_id exists
    existing_idx = next((i for i, r in enumerate(rows) if r['doc_id'] == doc_info['doc_id']), None)
    
    new_row = {
        "doc_id": doc_info['doc_id'],
        "source_file": doc_info['source_file'],
        "sha256": doc_info['sha256'],
        "pages": doc_info['pages'],
        "added_utc": doc_info['added_utc'],
        "notes": "",
        "license_ok": ""
    }
    
    if existing_idx is not None:
        # Update existing (keep notes/license if present)
        current = rows[existing_idx]
        new_row['notes'] = current.get('notes', '')
        new_row['license_ok'] = current.get('license_ok', '')
        rows[existing_idx] = new_row
    else:
        rows.append(new_row)
        
    with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["doc_id", "source_file", "sha256", "pages", "added_utc", "notes", "license_ok"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def ingest_pdfs(
    pdf_paths: list,
    output_dir: Path,
    manifest_path: Path,
    append: bool = False,
) -> int:
    """Ingest a list of PDF files into paragraphs.jsonl + paragraphs.csv.

    Args:
        pdf_paths: List of Path objects pointing to PDF files.
        output_dir: Directory for processed output (paragraphs.jsonl etc.).
        manifest_path: Path to the corpus manifest CSV.
        append: If True, append new paragraphs to existing files instead of
                overwriting. Use this when adding documents via the UI.

    Returns:
        Number of paragraphs produced from this batch.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_out = output_dir / "paragraphs.jsonl"
    csv_out = output_dir / "paragraphs.csv"
    ensure_manifest(manifest_path)

    if not pdf_paths:
        logger.warning("No PDF files provided.")
        return 0

    logger.info(f"Ingesting {len(pdf_paths)} PDF(s)...")

    all_paragraphs = []

    for pdf_file in tqdm(pdf_paths, desc="Ingesting PDFs"):
        pdf_file = Path(pdf_file)
        doc_id = pdf_file.stem.lower().replace(" ", "_")
        file_sha = get_file_sha256(pdf_file)

        try:
            pages = extract_text_from_pdf(str(pdf_file))
            num_pages = len(pages)

            update_manifest(manifest_path, {
                "doc_id": doc_id,
                "source_file": pdf_file.name,
                "sha256": file_sha,
                "pages": num_pages,
