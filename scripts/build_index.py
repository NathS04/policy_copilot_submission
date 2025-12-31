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
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            p = json.loads(line)
            paragraphs.append(p)
            texts.append(p['text'])

    if not texts:
        raise ValueError("No paragraphs found in corpus JSONL.")

    logger.info(f"Loaded {len(texts)} paragraphs.")

    logger.info("Generating embeddings (this may take a while)...")
    embeddings = embed_texts(texts)

    logger.info("Building FAISS index...")
    index = FaissIndex(dimension=embeddings.shape[1])
    index.add(embeddings, paragraphs)

    logger.info(f"Saving index to {index_dir}...")
    index.save(index_dir)
    logger.info("Done.")


def main():
    parser = argparse.ArgumentParser(description="Build FAISS index from processed corpus.")
    parser.add_argument("--input_path", default="data/corpus/processed/paragraphs.jsonl", help="Input JSONL path")
    parser.add_argument("--index_dir", default=settings.INDEX_DIR, help="Directory to save index")
    args = parser.parse_args()

    try:
        build_index(Path(args.input_path), Path(args.index_dir))
    except (ImportError, FileNotFoundError, ValueError) as exc:
        logger.error(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
