"""
Tests for abstention/confidence gating.
"""
from policy_copilot.verify.abstain import compute_confidence, should_abstain


class TestConfidenceComputation:
    def test_empty_evidence(self):
        """Empty evidence gives zero confidence."""
        conf = compute_confidence([])
        assert conf["max_rerank"] == 0.0
        assert conf["mean_top3_rerank"] == 0.0

    def test_single_evidence(self):
        """Single evidence item should set both metrics."""
        conf = compute_confidence([{"score_rerank": 0.75}])
        assert conf["max_rerank"] == 0.75
        assert conf["mean_top3_rerank"] == 0.75

    def test_multiple_evidence(self):
        """Multiple items: max should be highest, mean_top3 should be correct."""
        evidence = [
            {"score_rerank": 0.9},
            {"score_rerank": 0.7},
            {"score_rerank": 0.5},
            {"score_rerank": 0.3},
            {"score_rerank": 0.1},
        ]
        conf = compute_confidence(evidence)
        assert conf["max_rerank"] == 0.9
        expected_mean = round((0.9 + 0.7 + 0.5) / 3, 4)
        assert conf["mean_top3_rerank"] == expected_mean


class TestAbstention:
    def test_abstain_below_threshold(self):
        """Should abstain when max_rerank is below threshold."""
        conf = {"max_rerank": 0.20}
        assert should_abstain(conf, threshold=0.30) is True

    def test_no_abstain_above_threshold(self):
        """Should NOT abstain when max_rerank is above threshold."""
        conf = {"max_rerank": 0.50}
        assert should_abstain(conf, threshold=0.30) is False

    def test_abstain_at_exact_threshold(self):
        """Should NOT abstain at exactly the threshold (>= passes)."""
        conf = {"max_rerank": 0.30}
        assert should_abstain(conf, threshold=0.30) is False

    def test_abstain_zero_confidence(self):
        """Zero confidence should trigger abstention."""
        conf = {"max_rerank": 0.0}
        assert should_abstain(conf, threshold=0.01) is True
