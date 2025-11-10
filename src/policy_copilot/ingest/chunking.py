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
    """Split a large chunk on sentence boundaries.

    Tries to keep each resulting piece <= max_chars while splitting at
    sentence-ending punctuation (. ! ?) followed by a space.
    """
    if len(text) <= max_chars:
        return [text]

    # Sentence-split regex: look for '. ', '! ', '? ' as split points
    sentences = re.split(r'(?<=[.!?])\s+', text)
    pieces: List[str] = []
    current = ""

    for sent in sentences:
        if current and len(current) + len(sent) + 1 > max_chars:
            pieces.append(current.strip())
            current = sent
        else:
            current = f"{current} {sent}".strip() if current else sent

    if current.strip():
        pieces.append(current.strip())

    return pieces
