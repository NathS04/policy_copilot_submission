from .chunking import chunk_text_to_paragraphs
from .paragraph_ids import generate_paragraph_id

__all__ = ["extract_text_from_pdf", "chunk_text_to_paragraphs", "generate_paragraph_id"]


def extract_text_from_pdf(*args, **kwargs):
    # Lazy import keeps core installs light (pypdf lives in optional ingest extras).
    from .pdf_extract import extract_text_from_pdf as _extract_text_from_pdf
    return _extract_text_from_pdf(*args, **kwargs)
