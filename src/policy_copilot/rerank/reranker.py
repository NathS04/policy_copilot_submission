"""
Cross-encoder reranker for improving evidence quality.
Uses sentence-transformers CrossEncoder by default, with graceful fallback.
"""
import time
from typing import List, Dict
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

_cross_encoder = None
_model_loaded = False
_load_attempted = False


def _load_cross_encoder(model_name: str):
    """Loads the cross-encoder model lazily (singleton)."""
    global _cross_encoder, _model_loaded, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True
    try:
        from sentence_transformers import CrossEncoder
        logger.info(f"Loading cross-encoder: {model_name}")
        _cross_encoder = CrossEncoder(model_name)
        _model_loaded = True
    except Exception as e:
        logger.warning(f"Could not load CrossEncoder ({e}). Falling back to retrieval scores.")
        _model_loaded = False


class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        _load_cross_encoder(model_name)
        self.fallback = not _model_loaded

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Reranks candidate paragraphs using the cross-encoder.
        Each candidate dict should have 'text', 'paragraph_id', 'score' (retrieval).
        Returns top_k candidates sorted by rerank score descending,
        with 'score_rerank' and original 'score_retrieve' preserved.
        """
        if not candidates:
            return []

        t0 = time.time()

        # preserve original retrieval score under a different key
        for c in candidates:
            c["score_retrieve"] = c.get("score", 0.0)

        if self.fallback or not _model_loaded:
            # graceful fallback: just use retrieval scores
            logger.warning("RERANK_FALLBACK: using original retrieval scores")
            for c in candidates:
                c["score_rerank"] = c.get("score_retrieve", c.get("score", 0.0))
            
            # Sort descending because score is now similarity (higher=better)
            # Fix E: Ensure reverse=True
            sorted_candidates = sorted(candidates, key=lambda x: x["score_rerank"], reverse=True)
            result = sorted_candidates[:top_k]
            elapsed = (time.time() - t0) * 1000
            logger.info(f"Rerank (fallback) took {elapsed:.0f}ms")
            return result
            
        # Normal path
        pairs = [[query, c["text"]] for c in candidates]
        scores = _cross_encoder.predict(pairs)
        
        results = []
        for i, score in enumerate(scores):
            # Fix E: Normalize score to [0,1] using sigmoid
            # CrossEncoder returns unbounded logits usually
            import math
            def sigmoid(x):
                return 1 / (1 + math.exp(-x))
                
            raw = float(score)
            norm = sigmoid(raw)
            
            c = candidates[i].copy()
            c["score_rerank"] = norm
            c["score_rerank_raw"] = raw
            results.append(c)
            
        # Sort desc by new normalized score
        results = sorted(results, key=lambda x: x["score_rerank"], reverse=True)
        
        return results[:top_k]

        # build pairs for cross-encoder
        pairs = [(query, c.get("text", "")) for c in candidates]
        try:
            scores = _cross_encoder.predict(pairs)
        except Exception as e:
            logger.error(f"CrossEncoder prediction failed: {e}")
            for c in candidates:
                c["score_rerank"] = c["score_retrieve"]
            return sorted(candidates, key=lambda x: x["score_retrieve"])[:top_k]

        # attach rerank scores
        for c, s in zip(candidates, scores):
            c["score_rerank"] = float(s)

        # sort by rerank score descending (higher = more relevant)
        sorted_candidates = sorted(candidates, key=lambda x: x["score_rerank"], reverse=True)

        elapsed = (time.time() - t0) * 1000
        logger.info(f"Rerank ({len(candidates)} -> {top_k}) took {elapsed:.0f}ms")
        return sorted_candidates[:top_k]
