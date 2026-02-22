import hashlib

def generate_paragraph_id(doc_id: str, page: int, para_index: int, content: str) -> str:
    """
    Generates a stable ID: {doc_id}::p{page:04d}::i{para_index:04d}::{sha12}
    """
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
    return f"{doc_id}::p{page:04d}::i{para_index:04d}::{content_hash}"
