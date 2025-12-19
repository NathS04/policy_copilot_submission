"""
Cross-encoder reranker for improving evidence quality.

Purpose:
    Implements the second stage of the two-stage retrieve-and-rerank pipeline.
    The bi-encoder retriever (FAISS) returns the top-k candidates based on
    cosine similarity; this module rescores those candidates using a cross-encoder
    that jointly attends to the query and document, producing a more accurate
    relevance ranking.

Design decisions:
    - The cross-encoder model (ms-marco-MiniLM-L-6-v2, 22M parameters) was chosen
      for its balance of precision and latency. Larger cross-encoders (e.g.,
      ms-marco-TinyBERT-L-6, or the full-size BERT models) offer marginal precision
      gains (~1-2% on MS MARCO) but double inference time. For a corpus of <2000
      paragraphs with top-20 candidate sets, the smaller model is sufficient —
      confirmed by retrieval evaluation showing 73.9% Evidence Recall@5.
    - Scores are sigmoid-normalised to [0,1] from the raw cross-encoder logits.
      This enables a meaningful absolute threshold for the abstention gate (0.30),
      since raw logits are unbounded and their scale varies across models.
    - Lazy loading is used for the model to avoid import-time overhead in test
      suites and CLI scripts that don't invoke reranking. The singleton pattern
      ensures the model is loaded at most once per process.

# Considered ColBERT (late-interaction) as an alternative to full cross-encoding.
# ColBERT achieves near-cross-encoder precision at bi-encoder-like speed, but
# requires materialising per-token embeddings (~3x storage). For our small corpus
# the storage cost was acceptable, but the implementation complexity was not
# justified given the modest candidate-set sizes (20 candidates per query).
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
    """
    Loads the cross-encoder model as a process-wide singleton.

    Parameters:
        model_name: HuggingFace model identifier for the cross-encoder.

    Notes:
        Uses a global flag to ensure loading is attempted at most once. If
        loading fails (e.g., missing dependencies in a test environment),
        the reranker falls back to using raw retrieval scores.
    """
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
    """
    Cross-encoder reranker with graceful degradation.

    If the cross-encoder model cannot be loaded (missing torch, etc.), the
    reranker falls back to using the original retrieval similarity scores.
    This ensures the pipeline remains functional in test and CI environments
    where ML dependencies may not be installed.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        _load_cross_encoder(model_name)
        self.fallback = not _model_loaded

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Reranks candidate paragraphs using the cross-encoder.

        Parameters:
            query:      The user's natural-language question.
            candidates: List of evidence dicts from the retriever, each containing
                        'text', 'paragraph_id', and 'score' (retrieval similarity).
            top_k:      Number of candidates to return after reranking.

        Returns:
            Top-k candidates sorted by rerank score (descending), with
            'score_rerank' (normalised) and 'score_retrieve' (original) preserved.

        Design decision:
            Original retrieval scores are preserved under 'score_retrieve' so that
            downstream analysis can compare retrieval vs reranking quality. This
            is used in the ablation study (Section 4.6) where reranking is disabled
            and the pipeline falls back to retrieval scores alone.
        """
        if not candidates:
            return []

        t0 = time.time()

        # Preserve original retrieval score under a separate key for ablation analysis
        for c in candidates:
            c["score_retrieve"] = c.get("score", 0.0)

        if self.fallback or not _model_loaded:
            # Graceful degradation: use raw retrieval scores when cross-encoder unavailable
            logger.warning("RERANK_FALLBACK: using original retrieval scores")
            for c in candidates:
                c["score_rerank"] = c.get("score_retrieve", c.get("score", 0.0))
            sorted_candidates = sorted(candidates, key=lambda x: x["score_rerank"], reverse=True)
            result = sorted_candidates[:top_k]
            elapsed = (time.time() - t0) * 1000
            logger.info(f"Rerank (fallback) took {elapsed:.0f}ms")
            return result

        # Normal path: score each (query, candidate) pair with the cross-encoder
        pairs = [[query, c["text"]] for c in candidates]
        scores = _cross_encoder.predict(pairs)

        results = []
        for i, score in enumerate(scores):
            raw = float(score)
            # Sigmoid normalisation maps logits to [0,1] for threshold compatibility
            norm = _sigmoid(raw)

            c = candidates[i].copy()
            c["score_rerank"] = norm
            c["score_rerank_raw"] = raw  # retained for diagnostic analysis
            results.append(c)

        # Sort descending by normalised rerank score — higher = more relevant
        results = sorted(results, key=lambda x: x["score_rerank"], reverse=True)

        elapsed = (time.time() - t0) * 1000
        logger.info(f"Rerank ({len(candidates)} -> {top_k}) took {elapsed:.0f}ms")
        return results[:top_k]
