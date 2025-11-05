import re
from typing import List


def clean_paragraph(text: str) -> str:
    """
    Normalizes whitespace and fixes common issues in a paragraph.
    """
    # Fix hyphens that might have survived extraction
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _split_large_chunk(text: str, max_chars: int = 400) -> List[str]:
