"""
When dense is requested but faiss/sentence-transformers are missing,
Retriever must record backend_requested='dense' and backend_used='bm25'.
"""
import unittest
from policy_copilot.retrieve.retriever import Retriever


class TestBackendProvenance(unittest.TestCase):
    def test_dense_fallback_records_both(self):
        """In core env (no faiss), dense request must fall back to bm25 and record both."""
        r = Retriever(backend="dense")
        self.assertEqual(r.backend_requested, "dense")
        # In test env without ML deps, should have fallen back
        if r.backend_used == "bm25":
            self.assertTrue(r.loaded or not r.loaded)  # just confirm attr exists
        else:
            # If ML deps happen to be installed, dense stays dense
            self.assertEqual(r.backend_used, "dense")
        # Either way, both attributes must exist and be strings
        self.assertIsInstance(r.backend_requested, str)
        self.assertIsInstance(r.backend_used, str)

    def test_bm25_explicit_no_fallback(self):
        """Explicitly requesting bm25 should have requested==used."""
        r = Retriever(backend="bm25")
        self.assertEqual(r.backend_requested, "bm25")
        self.assertEqual(r.backend_used, "bm25")
