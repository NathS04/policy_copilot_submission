"""
Tests for the hybrid retriever (Reciprocal Rank Fusion).

Uses mock dense and sparse retrievers with known rankings to verify
deterministic fusion behaviour.
"""
import pytest
from unittest.mock import MagicMock

from policy_copilot.retrieve.hybrid import HybridRetriever


# ------------------------------------------------------------------ #
#  Fixtures                                                            #
# ------------------------------------------------------------------ #

def _make_results(ids_and_scores):
    """Build retriever-style results from (id, score) pairs."""
    return [
        {
            "paragraph_id": pid,
            "doc_id": "doc1",
            "page": 1,
            "text": f"Content for {pid}",
            "source_file": "test.pdf",
            "score": score,
            "backend": "test",
        }
        for pid, score in ids_and_scores
    ]


def _mock_retriever(results, loaded=True, is_ready=True):
    r = MagicMock()
    r.loaded = loaded
    r.is_ready = is_ready
    r.retrieve.return_value = results
    return r


# ------------------------------------------------------------------ #
#  Tests: RRF fusion formula                                           #
# ------------------------------------------------------------------ #

class TestRRFFusion:

    def test_rrf_merges_both_rankings(self):
        """RRF produces results from both dense and sparse."""
        dense = _make_results([("A", 0.9), ("B", 0.8), ("C", 0.7)])
        sparse = _make_results([("B", 0.95), ("D", 0.85), ("A", 0.75)])

        hybrid = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
            alpha=0.5, rrf_k=60,
        )
        results = hybrid.retrieve("test query", k=4)

        result_ids = [r["paragraph_id"] for r in results]
        assert "A" in result_ids
        assert "B" in result_ids
        assert len(results) == 4

    def test_rrf_scores_are_deterministic(self):
        """Same input rankings produce the same fused scores."""
        dense = _make_results([("A", 0.9), ("B", 0.8)])
        sparse = _make_results([("B", 0.95), ("A", 0.75)])

        h1 = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
            alpha=0.5, rrf_k=60,
        )
        h2 = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
            alpha=0.5, rrf_k=60,
        )

        r1 = h1.retrieve("q", k=2)
        r2 = h2.retrieve("q", k=2)

        for a, b in zip(r1, r2):
            assert a["fused_score"] == b["fused_score"]

    def test_rrf_formula_values(self):
        """Verify RRF scores match the expected formula: alpha/(k+rank_d) + (1-alpha)/(k+rank_s)."""
        dense = _make_results([("A", 0.9), ("B", 0.8)])
        sparse = _make_results([("B", 0.95), ("A", 0.75)])

        rrf_k = 60
        alpha = 0.5
        hybrid = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
            alpha=alpha, rrf_k=rrf_k,
        )
        results = hybrid.retrieve("q", k=2)

        scores = {r["paragraph_id"]: r["fused_score"] for r in results}

        # A: dense_rank=1, sparse_rank=2
        expected_a = alpha / (rrf_k + 1) + (1 - alpha) / (rrf_k + 2)
        assert abs(scores["A"] - round(expected_a, 6)) < 1e-5

        # B: dense_rank=2, sparse_rank=1
        expected_b = alpha / (rrf_k + 2) + (1 - alpha) / (rrf_k + 1)
        assert abs(scores["B"] - round(expected_b, 6)) < 1e-5

    def test_rrf_records_ranks(self):
        """Each result records its dense and sparse rank."""
        dense = _make_results([("A", 0.9), ("B", 0.8)])
        sparse = _make_results([("B", 0.95), ("C", 0.85)])

        hybrid = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
        )
        results = hybrid.retrieve("q", k=3)

        a_result = next(r for r in results if r["paragraph_id"] == "A")
        assert a_result["dense_rank"] == 1
        assert a_result["sparse_rank"] is None  # A not in sparse results

        b_result = next(r for r in results if r["paragraph_id"] == "B")
        assert b_result["dense_rank"] == 2
        assert b_result["sparse_rank"] == 1


# ------------------------------------------------------------------ #
#  Tests: alpha weighting                                              #
# ------------------------------------------------------------------ #

class TestRRFAlpha:

    def test_alpha_1_favours_dense(self):
        """alpha=1.0 makes sparse contribution zero."""
        dense = _make_results([("A", 0.9), ("B", 0.8)])
        sparse = _make_results([("C", 0.95), ("D", 0.85)])

        hybrid = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
            alpha=1.0,
        )
        results = hybrid.retrieve("q", k=2)

        top = results[0]["paragraph_id"]
        assert top == "A"

    def test_alpha_0_favours_sparse(self):
        """alpha=0.0 makes dense contribution zero."""
        dense = _make_results([("A", 0.9), ("B", 0.8)])
        sparse = _make_results([("C", 0.95), ("D", 0.85)])

        hybrid = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
            alpha=0.0,
        )
        results = hybrid.retrieve("q", k=2)

        top = results[0]["paragraph_id"]
        assert top == "C"


# ------------------------------------------------------------------ #
#  Tests: fallback behaviour                                           #
# ------------------------------------------------------------------ #

class TestHybridFallback:

    def test_dense_only_when_sparse_unavailable(self):
        """Falls back to dense-only when sparse is not ready."""
        dense = _make_results([("A", 0.9)])
        sparse_ret = _mock_retriever([], is_ready=False)

        hybrid = HybridRetriever(_mock_retriever(dense), sparse_ret)
        results = hybrid.retrieve("q", k=1)

        assert len(results) == 1
        assert results[0]["paragraph_id"] == "A"
        assert hybrid.fusion_method == "dense_only"

    def test_sparse_only_when_dense_unavailable(self):
        """Falls back to sparse-only when dense is not loaded."""
        dense_ret = _mock_retriever([], loaded=False)
        sparse = _make_results([("B", 0.85)])

        hybrid = HybridRetriever(dense_ret, _mock_retriever(sparse))
        results = hybrid.retrieve("q", k=1)

        assert len(results) == 1
        assert results[0]["paragraph_id"] == "B"
        assert hybrid.fusion_method == "sparse_only"

    def test_empty_when_both_unavailable(self):
        """Returns empty when neither backend is available."""
        hybrid = HybridRetriever(
            _mock_retriever([], loaded=False),
            _mock_retriever([], is_ready=False),
        )
        assert hybrid.loaded is False
        results = hybrid.retrieve("q", k=5)
        assert results == []


# ------------------------------------------------------------------ #
#  Tests: metadata recording                                           #
# ------------------------------------------------------------------ #

class TestHybridMetadata:

    def test_fusion_method_recorded(self):
        """Fusion method is recorded in results."""
        dense = _make_results([("A", 0.9)])
        sparse = _make_results([("B", 0.85)])

        hybrid = HybridRetriever(
            _mock_retriever(dense), _mock_retriever(sparse),
        )
        results = hybrid.retrieve("q", k=2)

        for r in results:
            assert r["fusion_method"] == "rrf"
            assert r["backend"] == "hybrid_rrf"

    def test_loaded_property(self):
        """loaded is True when at least one backend works."""
        hybrid = HybridRetriever(
            _mock_retriever(_make_results([("A", 0.9)])),
            _mock_retriever([], is_ready=False),
        )
        assert hybrid.loaded is True
