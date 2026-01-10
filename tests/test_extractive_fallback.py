
import unittest
from policy_copilot.generate.answerer import Answerer
from policy_copilot.config import settings

class TestExtractiveFallback(unittest.TestCase):
    def setUp(self):
        settings.ENABLE_LLM = False
        self.answerer = Answerer()

    def test_fallback_has_inline_citations(self):
        """Fallback response must have [CITATION: pid] appended to sentences."""
        question = "Q"
        evidence = [{
            "paragraph_id": "doc::p1", 
            "text": "Sentence one. Sentence two.", 
            "score": 0.9
        }]
        
        # B3 path (or B2 path now that we fixed it)
        # Using B3 as it's the primary user of verification
        resp, meta = self.answerer.generate_b3(question, evidence, allow_fallback=True)
        
        self.assertIn("[CITATION: doc::p1]", resp.answer)
        self.assertIn("Sentence one", resp.answer)
        self.assertIn("Sentence two", resp.answer)
        self.assertIn("doc::p1", resp.citations)

if __name__ == "__main__":
    unittest.main()
