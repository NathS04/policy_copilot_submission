
import unittest
from policy_copilot.generate.answerer import Answerer
from policy_copilot.config import settings

class TestExtractiveB2(unittest.TestCase):
    def setUp(self):
        # Disable LLM globally for this test
        self.original_llm_flag = settings.ENABLE_LLM
        settings.ENABLE_LLM = False
        self.answerer = Answerer()

    def tearDown(self):
        settings.ENABLE_LLM = self.original_llm_flag

    def test_extractive_b2_fallback_enabled(self):
        """B2 with allow_fallback=True must return relevant text, not LLM_DISABLED."""
        question = "Test question"
        evidence = [{
            "paragraph_id": "test_p1", 
            "text": "This is the fallback answer.", 
            "score": 0.9
        }]
        
        # Act
        resp, meta = self.answerer.generate_naive_rag(question, evidence, allow_fallback=True)
        
        # Assert
        self.assertNotEqual(resp.answer, "LLM_DISABLED")
        self.assertNotEqual(resp.answer, "INSUFFICIENT_EVIDENCE")
        self.assertIn("fallback answer", resp.answer)
        self.assertIn("test_p1", resp.citations)

    def test_extractive_b2_fallback_disabled(self):
        """B2 with allow_fallback=False (default behavior/strict) should return LLM_DISABLED or equivalent."""
        question = "Test question"
        evidence = [{
            "paragraph_id": "test_p1", 
            "text": "This is the fallback answer.", 
            "score": 0.9
        }]
        
        # Act
        resp, meta = self.answerer.generate_naive_rag(question, evidence, allow_fallback=False)
        
        # Assert
        self.assertEqual(resp.answer, "LLM_DISABLED")

if __name__ == "__main__":
    unittest.main()
