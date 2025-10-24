import re
from typing import List, Dict
import pypdf
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

def normalize_whitespace(text: str) -> str:
    """
    Collapses multiple spaces/newlines into single spaces, trims.
    """
    return re.sub(r'\s+', ' ', text).strip()

def fix_hyphenation(text: str) -> str:
    """
    Joins hyphenated words at line breaks (e.g., 'inter-\nnal' -> 'internal').
