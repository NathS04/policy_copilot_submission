"""Cross-encoder reranker.

The bi-encoder retriever returns a candidate set; this module rescores those
candidates with a cross-encoder that attends to the query and document
together. Raw cross-encoder logits are passed through a sigmoid so the
downstream abstention gate can use an absolute threshold.

The model is loaded lazily and kept as a process-wide singleton — that keeps
import-time cheap for CLI scripts and tests that never call rerank.
"""
import time
import math
from typing import List, Dict
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

# Singleton cross-encoder instance — loaded lazily on first rerank call
_cross_encoder = None
_model_loaded = False
_load_attempted = False


def _load_cross_encoder(model_name: str):
    """Load the cross-encoder once per process. Falls back silently if the
    transformers stack isn't installed (e.g. in lightweight test envs)."""
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


def _sigmoid(x: float) -> float:
    """Logistic sigmoid — maps unbounded logits to [0, 1] probability scale."""
    return 1 / (1 + math.exp(-x))


class Reranker:
    """Cross-encoder reranker. If the model can't load (CI, no torch),
    falls back to the original retrieval scores so the pipeline still runs."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        _load_cross_encoder(model_name)
        self.fallback = not _model_loaded

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
        """Rerank candidates and return the top-k.

        The original retrieval score is kept under ``score_retrieve`` and the
        new normalised cross-encoder score under ``score_rerank`` — the ablation
        runs read both keys.
        """
        if not candidates:
            return []

        t0 = time.time()

        for c in candidates:
            c["score_retrieve"] = c.get("score", 0.0)

        if self.fallback or not _model_loaded:
            logger.warning("RERANK_FALLBACK: using original retrieval scores")
            for c in candidates:
                c["score_rerank"] = c.get("score_retrieve", c.get("score", 0.0))
            sorted_candidates = sorted(candidates, key=lambda x: x["score_rerank"], reverse=True)
            result = sorted_candidates[:top_k]
            elapsed = (time.time() - t0) * 1000
            logger.info(f"Rerank (fallback) took {elapsed:.0f}ms")
            return result

        pairs = [[query, c["text"]] for c in candidates]
        scores = _cross_encoder.predict(pairs)

        results = []
        for i, score in enumerate(scores):
            raw = float(score)
            c = candidates[i].copy()
            c["score_rerank"] = _sigmoid(raw)
            c["score_rerank_raw"] = raw
            results.append(c)

        results.sort(key=lambda x: x["score_rerank"], reverse=True)

        elapsed = (time.time() - t0) * 1000
        logger.info(f"Rerank ({len(candidates)} -> {top_k}) took {elapsed:.0f}ms")
        return results[:top_k]
