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

