"""
Tests for golden set validation.
"""
import csv
import os
import sys

# ensure correct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.validate_golden_set import validate


class TestGoldenSetValidation:
    def test_valid_minimal(self, tmp_path):
        """A full valid row should pass."""
        gs = tmp_path / "gs.csv"
        with open(gs, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_id", "question", "category", "split",
                        "gold_doc_ids", "gold_paragraph_ids", "notes"])
            # 60+ rows needed to pass size check — write 60 answerable + 1 unanswerable
            for i in range(50):
                w.writerow([f"q_{i:03d}", f"Question {i}?", "answerable",
                            "test", "doc1", "p1", ""])
            for i in range(10):
                w.writerow([f"q_u{i:03d}", f"Unanswerable {i}?", "unanswerable",
                            "test", "", "", ""])
            # 1 contradiction with 2+ gold IDs
            w.writerow(["q_c001", "Conflict?", "contradiction", "dev",
                         "doc1,doc2", "p1,p2", ""])

        errors = validate(str(gs))
        assert len(errors) == 0, f"Expected no errors but got: {errors}"

    def test_duplicate_query_id(self, tmp_path):
        """Duplicate query_id should fail."""
        gs = tmp_path / "gs.csv"
        with open(gs, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_id", "question", "category", "split",
                        "gold_doc_ids", "gold_paragraph_ids", "notes"])
            w.writerow(["q_001", "Question 1?", "answerable", "test", "d1", "p1", ""])
            w.writerow(["q_001", "Question 2?", "answerable", "test", "d1", "p2", ""])

        errors = validate(str(gs))
        assert any("duplicate" in e.lower() for e in errors)

    def test_answerable_without_gold_ids(self, tmp_path):
        """Answerable with empty gold_paragraph_ids should fail."""
        gs = tmp_path / "gs.csv"
        with open(gs, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_id", "question", "category", "split",
                        "gold_doc_ids", "gold_paragraph_ids", "notes"])
            w.writerow(["q_001", "Question?", "answerable", "test", "", "", ""])

        errors = validate(str(gs))
        assert any("gold_paragraph_ids" in e for e in errors)

    def test_contradiction_needs_two_ids(self, tmp_path):
        """Contradiction with <2 gold IDs should fail."""
        gs = tmp_path / "gs.csv"
        with open(gs, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_id", "question", "category", "split",
                        "gold_doc_ids", "gold_paragraph_ids", "notes"])
            w.writerow(["q_001", "Contradiction?", "contradiction", "test",
                         "d1", "p1", ""])

        errors = validate(str(gs))
        assert any("≥2" in e for e in errors)

    def test_invalid_split(self, tmp_path):
        """Invalid split should fail."""
        gs = tmp_path / "gs.csv"
        with open(gs, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_id", "question", "category", "split",
                        "gold_doc_ids", "gold_paragraph_ids", "notes"])
            w.writerow(["q_001", "Question?", "answerable", "INVALID",
                         "d1", "p1", ""])

        errors = validate(str(gs))
        assert any("split" in e.lower() for e in errors)

    def test_unanswerable_with_gold_ids(self, tmp_path):
        """Unanswerable with gold_paragraph_ids should fail."""
        gs = tmp_path / "gs.csv"
        with open(gs, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["query_id", "question", "category", "split",
                        "gold_doc_ids", "gold_paragraph_ids", "notes"])
            w.writerow(["q_001", "Question?", "unanswerable", "test",
                         "", "p1", ""])

        errors = validate(str(gs))
        assert any("unanswerable" in e.lower() for e in errors)
