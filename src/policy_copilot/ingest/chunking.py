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


def chunk_text_to_paragraphs(page_text: str) -> List[str]:
    """
    Splits page text into paragraphs.
    Heuristic: Double newlines usually mean new paragraph in raw extraction.
    Large chunks are further split on sentence boundaries (~400 chars).
    """
    # Normalize line endings
    text = page_text.replace('\r\n', '\n').replace('\r', '\n')

    # Split by double newline (common visual paragraph break)
    raw_blocks = text.split('\n\n')
    paragraphs = []

    for block in raw_blocks:
        # Join inner lines of the block
        joined = block.replace('\n', ' ')
        cleaned = clean_paragraph(joined)

        # Filter out empty or very short noise (e.g. page numbers)
        if len(cleaned) > 20:
            # Sub-split large chunks on sentence boundaries
            for piece in _split_large_chunk(cleaned, max_chars=400):
                if len(piece) > 20:
                    paragraphs.append(piece)

    return paragraphs
