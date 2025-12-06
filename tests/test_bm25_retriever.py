
import unittest
import tempfile
import json
from pathlib import Path
from policy_copilot.retrieve.bm25_retriever import BM25Retriever

class TestBM25Retriever(unittest.TestCase):
    def setUp(self):
        # Create a temporary paragraphs.jsonl
        self.temp_dir = tempfile.TemporaryDirectory()
        self.paragraphs_path = Path(self.temp_dir.name) / "paragraphs.jsonl"
        
        self.data = [
            {"paragraph_id": "doc::p1", "text": "This is a paragraph about remote work policies.", "id": "wrong_key"},
            {"paragraph_id": "doc::p2", "text": "Security protocols are strict here.", "doc_id": "d2"},
            {"id": "doc::p3", "text": "Another remote work mention.", "doc_id": "d3"}, # check fallback
        ]
        
        with open(self.paragraphs_path, "w") as f:
            for p in self.data:
                f.write(json.dumps(p) + "\n")
                
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_retrieve_returns_correct_ids_and_scores(self):
        retriever = BM25Retriever(str(self.paragraphs_path))
        results = retriever.retrieve("remote work", k=2)
        
        self.assertTrue(len(results) > 0)
        
        for r in results:
            # Check ID is present and correct pattern
            pid = r.get("paragraph_id")
            self.assertTrue(pid, "paragraph_id must not be empty")
            self.assertIn("doc::p", pid)
            
            # Check score normalization
            score = r.get("score")
            self.assertIsInstance(score, float)
            self.assertTrue(0.0 <= score <= 1.0, f"Score {score} not in [0,1]")
            
            # Check raw score exists
            self.assertIn("score_raw", r)
            self.assertGreaterEqual(r["score_raw"], 0.0)

if __name__ == "__main__":
    unittest.main()
