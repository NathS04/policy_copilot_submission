"""
Unit test: B3 generative path returns (resp, meta) with valid Response when LLM is available.
Monkeypatch _check_llm_available -> True and _call_llm -> valid JSON; assert generate_b3 returns non-None.
"""
import unittest
from unittest.mock import patch

from policy_copilot.generate.answerer import Answerer
from policy_copilot.generate.schema import RAGResponse


def _stub_call_llm(system: str, user: str):
    """Return valid JSON so that generate_b3 parses and returns a Response."""
    return '{"answer": "ok", "citations": ["p1"], "notes": null}', {"prompt_tokens": 1, "completion_tokens": 1}, 10.0


class TestAnswererB3Generative(unittest.TestCase):
    def setUp(self):
        self.answerer = Answerer()

    @patch("policy_copilot.generate.answerer._call_llm", side_effect=_stub_call_llm)
    @patch.object(Answerer, "_check_llm_available", return_value=True)
    def test_generate_b3_returns_non_none_with_llm(
        self, mock_check_llm, mock_call_llm
    ):
        """When LLM is available and allow_fallback=False, generate_b3 must return (resp, meta) with real answer."""
        question = "What is the policy?"
        evidence = [
            {"paragraph_id": "p1", "text": "The policy says X.", "score": 0.9},
        ]
        resp, meta = self.answerer.generate_b3(question, evidence, allow_fallback=False)

        self.assertIsNotNone(resp, "generate_b3 must not return None")
        self.assertIsInstance(resp, RAGResponse)
        self.assertEqual(resp.answer, "ok")
        self.assertIsInstance(resp.citations, list)
        self.assertIn("p1", resp.citations)
        self.assertIsNotNone(meta)
        self.assertIn("latency_ms", meta)
        self.assertIn("confidence", meta, "meta must contain confidence (can be dummy)")
        self.assertIn("tokens", meta, "meta must contain tokens (can be dummy)")
        self.assertFalse(meta.get("fallback_used", True), "LLM path should not set fallback_used True")

    @patch.object(Answerer, "_check_llm_available", return_value=False)
    def test_generate_b3_extractive_fallback_returns_non_none(self, mock_check_llm):
        """When LLM is unavailable and allow_fallback=True with relevant evidence, generate_b3 must return extractive fallback."""
        question = "What encryption requirements apply to sensitive data?"
        evidence = [
            {"paragraph_id": "p1", "text": "Encryption of sensitive data at rest is mandatory. Data in transit must use TLS.", "score": 0.9},
        ]
        resp, meta = self.answerer.generate_b3(question, evidence, allow_fallback=True)

        self.assertIsNotNone(resp)
        self.assertNotEqual(resp.answer, "LLM_DISABLED")
        self.assertIn("ncryption", resp.answer)
        self.assertIn("p1", resp.citations)
        self.assertTrue(meta.get("fallback_used", False))


if __name__ == "__main__":
    unittest.main()
