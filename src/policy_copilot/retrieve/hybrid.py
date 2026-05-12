"""Hybrid retriever — fuses dense (FAISS) and sparse (BM25) results via RRF.

Dense and sparse scores live on incompatible scales (L2 distance vs BM25
Okapi), so we fuse by rank rather than by raw score. ``alpha`` lets us
weight one backend over the other; ``alpha=0.5`` is plain RRF.
"""
from __future__ import annotations

from typing import Any, Dict, List

from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


class HybridRetriever:
    """Reciprocal Rank Fusion over dense and sparse retrievers.

    Both backends just need a ``retrieve(query, k=...)`` method that returns
    a list of dicts. ``alpha`` is the dense weight (sparse gets ``1 - alpha``)
    and ``rrf_k`` is the RRF smoothing constant — 60 is the usual default.
    """

    fusion_method: str = "rrf"

    def __init__(
        self,
        dense_retriever: Any,
        sparse_retriever: Any,
        alpha: float = 0.5,
        rrf_k: int = 60,
    ):
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.alpha = alpha
        self.rrf_k = rrf_k

        self._dense_ok = getattr(dense_retriever, "loaded", False) if dense_retriever else False
        self._sparse_ok = getattr(sparse_retriever, "is_ready", False) if sparse_retriever else False

        if self._dense_ok and self._sparse_ok:
            self.fusion_method = "rrf"
        elif self._dense_ok:
            self.fusion_method = "dense_only"
        elif self._sparse_ok:
            self.fusion_method = "sparse_only"
        else:
            self.fusion_method = "none"

    @property
    def loaded(self) -> bool:
        return self._dense_ok or self._sparse_ok

    @property
    def backend(self) -> str:
        return self.fusion_method

    @property
    def backend_used(self) -> str:
        return self.fusion_method

    @property
    def backend_requested(self) -> str:
        return "hybrid"

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve and fuse results from both backends.

        Falls back to whichever single backend is available if the other
        is not loaded.
        """
        if not self.loaded:
            logger.error("HybridRetriever: no backend available.")
            return []

        dense_results: List[Dict] = []
        sparse_results: List[Dict] = []
        fetch_k = max(k * 4, 20)

        if self._dense_ok:
            try:
                dense_results = self.dense.retrieve(query, k=fetch_k)
            except Exception as exc:
                logger.warning("Dense retrieval failed in hybrid: %s", exc)
                self._dense_ok = False

        if self._sparse_ok:
            try:
                sparse_results = self.sparse.retrieve(query, k=fetch_k)
            except Exception as exc:
                logger.warning("Sparse retrieval failed in hybrid: %s", exc)
                self._sparse_ok = False

        if dense_results and sparse_results:
            self.fusion_method = "rrf"
            return self._fuse_rrf(dense_results, sparse_results, k)

        if dense_results:
            self.fusion_method = "dense_only"
            return self._annotate_single(dense_results[:k], source="dense")

        if sparse_results:
            self.fusion_method = "sparse_only"
            return self._annotate_single(sparse_results[:k], source="sparse")

        return []

    def _fuse_rrf(
        self,
        dense_results: List[Dict],
        sparse_results: List[Dict],
        k: int,
    ) -> List[Dict]:
        """Apply weighted Reciprocal Rank Fusion."""
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}
        all_docs: Dict[str, Dict] = {}

        for rank, doc in enumerate(dense_results, start=1):
            pid = doc.get("paragraph_id", "")
            if not pid:
                continue
            dense_ranks[pid] = rank
            if pid not in all_docs:
                all_docs[pid] = doc.copy()
            all_docs[pid]["score_dense"] = doc.get("score", 0.0)

        for rank, doc in enumerate(sparse_results, start=1):
            pid = doc.get("paragraph_id", "")
            if not pid:
                continue
            sparse_ranks[pid] = rank
            if pid not in all_docs:
                all_docs[pid] = doc.copy()
            all_docs[pid]["score_sparse"] = doc.get("score", 0.0)

        fused_scores: Dict[str, float] = {}
        alpha = self.alpha
        rrf_k = self.rrf_k
        max_rank = len(dense_results) + len(sparse_results) + 1

        for pid in all_docs:
            d_rank = dense_ranks.get(pid, max_rank)
            s_rank = sparse_ranks.get(pid, max_rank)

            score = (
                alpha / (rrf_k + d_rank)
                + (1.0 - alpha) / (rrf_k + s_rank)
            )
            fused_scores[pid] = score

        ranked = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Dict] = []
        for pid, fused_score in ranked[:k]:
            doc = all_docs[pid]
            doc["score"] = fused_score
            doc["fused_score"] = round(fused_score, 6)
            doc["dense_rank"] = dense_ranks.get(pid)
            doc["sparse_rank"] = sparse_ranks.get(pid)
            doc["backend"] = "hybrid_rrf"
            doc["fusion_method"] = "rrf"
            doc["fusion_alpha"] = alpha
            doc["fusion_rrf_k"] = rrf_k
            results.append(doc)

        logger.info(
            "Hybrid RRF: %d dense + %d sparse -> %d unique -> top %d",
            len(dense_results), len(sparse_results), len(all_docs), len(results),
        )
        return results

    @staticmethod
    def _annotate_single(
        results: List[Dict], source: str,
    ) -> List[Dict]:
        for doc in results:
            doc["backend"] = source
            doc["fusion_method"] = f"{source}_only"
            doc["dense_rank"] = None
            doc["sparse_rank"] = None
            doc["fused_score"] = None
        return results
