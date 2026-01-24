"""
When the top evidence paragraph IS relevant to the question,
B3 extractive fallback must return a real answer (not INSUFFICIENT_EVIDENCE).
"""
import unittest
from policy_copilot.generate.answerer import Answerer
from policy_copilot.config import settings


class TestB3FallbackRelevancePass(unittest.TestCase):
    def setUp(self):
        self._orig = settings.ENABLE_LLM
        settings.ENABLE_LLM = False

    def tearDown(self):
        settings.ENABLE_LLM = self._orig

    def test_relevant_paragraph_returns_answer(self):
        """Encryption question + encryption text => real answer."""
        a = Answerer()
        question = "What encryption requirements apply to sensitive data?"
        evidence = [{
            "paragraph_id": "it_security::p0009",
            "text": "Encryption of sensitive data at rest is mandatory using AES-256 or equivalent. Data in transit must be protected using TLS 1.3.",
            "score": 0.9,
        }]
        resp, meta = a.generate_b3(question, evidence, allow_fallback=True)
        self.assertNotEqual(resp.answer, "INSUFFICIENT_EVIDENCE")
        self.assertIn("encryption", resp.answer.lower())
