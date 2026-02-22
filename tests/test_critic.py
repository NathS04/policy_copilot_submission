"""
Tests for the critic agent (heuristic mode).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from policy_copilot.critic.critic_agent import detect_heuristic
from policy_copilot.critic.labels import LABELS, LABEL_IDS


class TestCriticLabels:
    def test_all_labels_defined(self):
        assert len(LABELS) == 6
        assert LABEL_IDS == ["L1", "L2", "L3", "L4", "L5", "L6"]

    def test_each_label_has_fields(self):
        for lid, ldef in LABELS.items():
            assert "name" in ldef
            assert "description" in ldef
            assert "examples" in ldef
            assert len(ldef["examples"]) > 0


class TestCriticHeuristic:
    def test_neutral_text_no_labels(self):
        result = detect_heuristic("All employees must adhere to data classification procedures.")
        assert result["labels"] == []

    def test_l1_normative_obviously(self):
        result = detect_heuristic("Obviously, this is the right approach.")
        assert "L1" in result["labels"]

    def test_l1_everyone_knows(self):
        result = detect_heuristic("Everyone knows this is necessary.")
        assert "L1" in result["labels"]

    def test_l2_merely(self):
        result = detect_heuristic("This regulation is merely a formality.")
        assert "L2" in result["labels"]

    def test_l2_only_a(self):
        result = detect_heuristic("It is only a minor concern.")
        assert "L2" in result["labels"]

    def test_l3_guarantees(self):
        result = detect_heuristic("This approach guarantees zero incidents.")
        assert "L3" in result["labels"]

    def test_l3_eliminates_all(self):
        result = detect_heuristic("This eliminates all risk.")
        assert "L3" in result["labels"]

    def test_l4_contradiction_must(self):
        result = detect_heuristic("Work must be approved. Remote work must not require approval.")
        assert "L4" in result["labels"]

    def test_l4_allowed_not_allowed(self):
        result = detect_heuristic("USB is allowed. USB is not allowed.")
        assert "L4" in result["labels"]

    def test_l5_either_or(self):
        result = detect_heuristic("We must choose between full surveillance or total vulnerability.")
        assert "L5" in result["labels"]

    def test_l6_inevitably(self):
        result = detect_heuristic("This will inevitably lead to collapse.")
        assert "L6" in result["labels"]

    def test_l6_dangerous_precedent(self):
        result = detect_heuristic("This sets a dangerous precedent for all future decisions.")
        assert "L6" in result["labels"]

    def test_multi_label(self):
        text = "Obviously the only two choices are to either ban all devices or accept inevitable leaks."
        result = detect_heuristic(text)
        assert "L1" in result["labels"]
        assert "L5" in result["labels"]

    def test_returns_rationales(self):
        result = detect_heuristic("Obviously this is wrong.")
        assert "L1" in result["rationales"]
        assert "obviously" in result["rationales"]["L1"]


class TestCriticMetrics:
    def test_basic_computation(self):
        from eval.metrics.critic_metrics import compute_critic_metrics

        gold = [["L1"], ["L2"], [], ["L1", "L3"]]
        pred = [["L1"], ["L2", "L4"], [], ["L1"]]
        labels = ["L1", "L2", "L3", "L4", "L5", "L6"]

        result = compute_critic_metrics(gold, pred, labels)

        assert result["per_label"]["L1"]["tp"] == 2
        assert result["per_label"]["L1"]["fp"] == 0
        assert result["per_label"]["L1"]["fn"] == 0
        assert result["per_label"]["L1"]["precision"] == 1.0
        assert result["per_label"]["L1"]["recall"] == 1.0

        assert result["per_label"]["L3"]["fn"] == 1  # missed L3
        assert result["per_label"]["L4"]["fp"] == 1  # false positive L4

        assert result["exact_match_accuracy"] == 0.5  # 2 out of 4

    def test_empty_input(self):
        from eval.metrics.critic_metrics import compute_critic_metrics
        result = compute_critic_metrics([], [], ["L1"])
        assert result["macro_f1"] == 0.0
        assert result["exact_match_accuracy"] == 0.0

    def test_perfect_score(self):
        from eval.metrics.critic_metrics import compute_critic_metrics
        gold = [["L1", "L2"], ["L3"]]
        pred = [["L1", "L2"], ["L3"]]
        labels = ["L1", "L2", "L3"]
        result = compute_critic_metrics(gold, pred, labels)
        assert result["macro_f1"] == 1.0
        assert result["exact_match_accuracy"] == 1.0
