import re
from typing import List, Dict
import pypdf
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def _fix_hyphenation(text: str) -> str:
    """Join words split across a line break by a hyphen."""
    return re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract text from a PDF, returning one dict per page with 'page' (1-based)
    and 'text'. Pages with no extractable text are skipped.
    """
    results: List[Dict] = []
    try:
        reader = pypdf.PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
            cleaned = _fix_hyphenation(text.replace('\x00', ''))
            results.append({"page": i + 1, "text": cleaned})
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return []

    return results
