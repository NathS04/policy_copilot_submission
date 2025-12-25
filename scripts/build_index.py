import argparse
import json
import sys
from pathlib import Path

from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def build_index(input_path: Path, index_dir: Path) -> None:
    """Read paragraphs JSONL, embed texts, build FAISS index, and save.

    Args:
        input_path: Path to the paragraphs.jsonl file.
        index_dir:  Directory to write the FAISS index artefacts into.

    Raises:
        SystemExit: If ML deps are missing or the input file is empty/absent.
    """
    # Fail fast: check ML deps BEFORE reading corpus
    try:
        from policy_copilot.index.embeddings import embed_texts
        from policy_copilot.index.faiss_index import FaissIndex
    except ImportError:
        logger.error("Dense indexing requires extras: pip install -e '.[ml]'")
        raise

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info("Reading corpus...")
    paragraphs = []
    texts = []
