import re
from typing import List


def clean_paragraph(text: str) -> str:
    """
    Normalizes whitespace and fixes common issues in a paragraph.
    """
