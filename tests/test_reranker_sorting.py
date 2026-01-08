
import unittest
import sys
from unittest.mock import MagicMock, patch

# We need to ensure we get a fresh Reranker class each time or reset its global state
# The Reranker module has globals: _cross_encoder, _model_loaded, _load_attempted

class TestRerankerSorting(unittest.TestCase):
    def setUp(self):
        # Reset globals in policy_copilot.rerank.reranker
        if "policy_copilot.rerank.reranker" in sys.modules:
            del sys.modules["policy_copilot.rerank.reranker"]

    def test_fallback_sorts_descending(self):
        # Patch before import
        with patch.dict(sys.modules, {"sentence_transformers": None}):
            from policy_copilot.rerank.reranker import Reranker
            
            candidates = [
                {"paragraph_id": "p1", "score": 0.1, "text": "low"},
                {"paragraph_id": "p2", "score": 0.9, "text": "high"},
                {"paragraph_id": "p3", "score": 0.5, "text": "mid"},
            ]
            
            reranker = Reranker(model_name="dummy")
            results = reranker.rerank("query", candidates, top_k=3)
            
            self.assertEqual(results[0]["paragraph_id"], "p2")
            self.assertEqual(results[1]["paragraph_id"], "p3")
            self.assertEqual(results[2]["paragraph_id"], "p1")

    def test_reranker_scores_normalized(self):
        # Mock successful load
        mock_ce_cls = MagicMock()
        mock_model = MagicMock()
        mock_model.predict.return_value = [5.0] # High logit
        mock_ce_cls.return_value = mock_model
        
        # We need to mock sentence_transformers such that import works
        mock_st = MagicMock()
        mock_st.CrossEncoder = mock_ce_cls
        
        with patch.dict(sys.modules, {"sentence_transformers": mock_st}):
            from policy_copilot.rerank.reranker import Reranker
            # Force global reload or manual set because _load_cross_encoder might have failed in prev test
            import policy_copilot.rerank.reranker as reranker_mod
            reranker_mod._model_loaded = True
            reranker_mod._cross_encoder = mock_model
            
            candidates = [{"paragraph_id": "p1", "text": "test", "score": 0.5}]
            
            reranker = Reranker(model_name="dummy")
            # The production code uses internal global _cross_encoder, not self.model
            # But wait, my previous edit used self.model? Let's check reranker.py
            results = reranker.rerank("query", candidates, top_k=1)
            
            self.assertIn("score_rerank", results[0])
            score = results[0]["score_rerank"]
            self.assertTrue(0.0 <= score <= 1.0)
            self.assertTrue(score > 0.99) # sigmoid(5) is close to 1

if __name__ == "__main__":
    unittest.main()
