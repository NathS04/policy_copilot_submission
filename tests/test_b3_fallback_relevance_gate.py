"""
When the top evidence paragraph is irrelevant to the question,
B3 extractive fallback must return INSUFFICIENT_EVIDENCE.
"""
import unittest
from policy_copilot.generate.answerer import Answerer
from policy_copilot.config import settings


class TestB3FallbackRelevanceGate(unittest.TestCase):
    def setUp(self):
        self._orig = settings.ENABLE_LLM
        settings.ENABLE_LLM = False

    def tearDown(self):
        settings.ENABLE_LLM = self._orig

    def test_irrelevant_paragraph_returns_insufficient(self):
        """Holiday question + DPIA text => INSUFFICIENT_EVIDENCE."""
        a = Answerer()
        question = "What is the company holiday allowance?"
        evidence = [{
            "paragraph_id": "dpia_guide::p0004",
            "text": "DPIA Process Step 1 -- Describe the Processing: Document what personal data is collected, from whom, for what purpose.",
            "score": 0.3,
        }]
        resp, meta = a.generate_b3(question, evidence, allow_fallback=True)
        self.assertEqual(resp.answer, "INSUFFICIENT_EVIDENCE")
        self.assertIn("FALLBACK_RELEVANCE_FAIL", resp.notes or "")
