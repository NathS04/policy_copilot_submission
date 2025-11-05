import json
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
from rank_bm25 import BM25Okapi
from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

class BM25Retriever:
    """
    Lightweight keyword-based retriever using BM25.
    Requires NO heavy ML dependencies (torch/transformers).
    """
    def __init__(self, paragraphs_path: Optional[str] = None):
        self.paragraphs = []
        self.bm25 = None
        self.is_ready = False
        
        path = Path(paragraphs_path) if paragraphs_path else settings.PROCESSED_DATA_DIR / "paragraphs.jsonl"
        if path.exists():
            self._build_index(path)
        else:
            logger.warning(f"BM25Retriever: Paragraphs file not found at {path}")

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split()

    def _build_index(self, path: Path):
        logger.info(f"Building BM25 index from {path}...")
        try:
            # Need to load paragraphs into memory
            with open(path, "r") as f:
                self.paragraphs = [json.loads(line) for line in f]
            
            tokenized_corpus = [self._tokenize(p.get("text", "")) for p in self.paragraphs]
            self.bm25 = BM25Okapi(tokenized_corpus)
            self.is_ready = True
            logger.info(f"BM25 index built with {len(self.paragraphs)} documents.")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        if not self.is_ready:
            logger.error("BM25 index not ready.")
            return []
            
        tokenized_query = self._tokenize(query)
        # Get top-k scores
        doc_scores = self.bm25.get_scores(tokenized_query)
        top_n = np.argsort(doc_scores)[::-1][:k]
        
        # Calculate max score for normalization (avoid div-by-zero)
        max_s = np.max(doc_scores) if len(doc_scores) > 0 else 1.0
        if max_s <= 1e-9:
             max_s = 1.0

        results = []
        for idx in top_n:
            raw_score = float(doc_scores[idx])
            norm_score = raw_score / max_s
            
            p = self.paragraphs[idx]
            # Fix A: Robust ID extraction
            pid = p.get("paragraph_id") or p.get("id") or ""
            
            results.append({
                "score": norm_score,
                "score_raw": raw_score,
                "paragraph_id": pid,
                "doc_id": p.get("doc_id", ""),
                "page": p.get("page", 0),
                "text": p.get("text", ""),
                "source_file": p.get("source_file", ""),
                "backend": "bm25" 
            })
        return results
