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
