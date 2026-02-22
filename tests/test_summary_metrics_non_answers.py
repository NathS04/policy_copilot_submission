"""
Unit test: answer_rate must NOT count LLM_DISABLED, ERROR, or INSUFFICIENT_EVIDENCE as answered.
"""
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_eval import NON_ANSWERS, _write_summary_metrics


class TestSummaryMetricsNonAnswers(unittest.TestCase):
    def test_answer_rate_excludes_non_answers(self):
        """Build a tiny fake outputs list; assert answer_rate counts only real text answers."""
        run_dir = Path(tempfile.mkdtemp())
        run_dir.mkdir(parents=True, exist_ok=True)

        # 4 answerable queries: 1 real answer, 1 LLM_DISABLED, 1 ERROR, 1 INSUFFICIENT_EVIDENCE
        records = [
            {"category": "answerable", "answer": "The policy states that X.", "citations": ["p1"], "gold_paragraph_ids": "p1"},
            {"category": "answerable", "answer": "LLM_DISABLED", "citations": [], "gold_paragraph_ids": "p1"},
            {"category": "answerable", "answer": "ERROR", "citations": [], "gold_paragraph_ids": "p1"},
            {"category": "answerable", "answer": "INSUFFICIENT_EVIDENCE", "citations": [], "gold_paragraph_ids": "p1"},
        ]

        _write_summary_metrics(run_dir, records, "b2")

        with open(run_dir / "summary.json") as f:
            summary = json.load(f)

        # answer_rate = 1/4 = 0.25 (only the first record is "answered"; LLM_DISABLED/ERROR/INSUFFICIENT_EVIDENCE must not count)
        self.assertEqual(summary["total_queries"], 4)
        self.assertEqual(summary["answer_rate"], 0.25)

    def test_non_answers_constant(self):
        """NON_ANSWERS must contain the three sentinel values and None."""
        self.assertIn("INSUFFICIENT_EVIDENCE", NON_ANSWERS)
        self.assertIn("LLM_DISABLED", NON_ANSWERS)
        self.assertIn("ERROR", NON_ANSWERS)
        self.assertIn(None, NON_ANSWERS)


if __name__ == "__main__":
    unittest.main()
