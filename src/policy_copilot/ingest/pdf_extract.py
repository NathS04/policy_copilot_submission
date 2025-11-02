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
    """
    return re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)

def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extracts text from a PDF file page by page.
    Returns: List[Dict] with 'page' (1-based) and 'text'.
    """
    results = []
    try:
        reader = pypdf.PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                # Basic cleanup before further processing
                # We fix hyphenation first (as newlines matter there)
                # But pypdf might not give perfect newlines.
                # Heuristic: replace hyphen followed by space/newline with nothing if it looks like a word break?
                # Actually, pypdf often processes layout. Let's try a simple approach first.
                clean_text = text.replace('\x00', '') # Remove null bytes
                results.append({
                    "page": i + 1,
                    "text": clean_text
                })
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return []
        
    return results
