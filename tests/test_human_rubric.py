"""
Tests for the human rubric import workflow (Cohen's kappa).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.import_human_eval_pack import _cohens_kappa, _compute_summary


class TestCohensKappa:
    def test_perfect_agreement(self):
        a = ["yes", "no", "yes", "no"]
        b = ["yes", "no", "yes", "no"]
        assert _cohens_kappa(a, b) == 1.0

    def test_no_agreement(self):
        a = ["yes", "yes", "yes", "yes"]
        b = ["no", "no", "no", "no"]
        kappa = _cohens_kappa(a, b)
        assert kappa <= 0  # at or below chance

    def test_partial_agreement(self):
        a = ["yes", "no", "yes", "no", "yes"]
        b = ["yes", "no", "no", "no", "yes"]
        kappa = _cohens_kappa(a, b)
        assert 0 < kappa < 1

    def test_empty_returns_zero(self):
        assert _cohens_kappa([], []) == 0.0

    def test_all_same_returns_one(self):
        a = ["yes", "yes", "yes"]
        b = ["yes", "yes", "yes"]
        assert _cohens_kappa(a, b) == 1.0


class TestComputeSummary:
    def test_basic_summary(self):
        items = [
            {
                "scores": {
                    "G0_ungrounded_present": False,
                    "G1_support_ratio": 0.8,
                    "G2_citation_correctness": 2,
                    "U1_answer_clarity": 4,
                    "U2_actionability": 3,
                }
            },
            {
                "scores": {
                    "G0_ungrounded_present": True,
                    "G1_support_ratio": 0.5,
                    "G2_citation_correctness": 1,
                    "U1_answer_clarity": 2,
                    "U2_actionability": 1,
                }
            },
        ]
        summary = _compute_summary(items)
        assert summary["total_scored"] == 2
        assert summary["ungrounded_rate"] == 0.5  # 1/2
        assert summary["mean_support_ratio"] == 0.65  # (0.8+0.5)/2
        assert summary["mean_clarity"] == 3.0  # (4+2)/2

    def test_no_scores(self):
        summary = _compute_summary([{"scores": None}])
        assert "error" in summary
