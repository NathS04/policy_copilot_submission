"""
build_index.py must exit with code 2 when ML deps (faiss, sentence-transformers) are missing.
"""
import subprocess
import sys
import unittest
from pathlib import Path


class TestBuildIndexMissingML(unittest.TestCase):
    def test_exits_2_without_ml_deps(self):
        root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "scripts/build_index.py",
             "--input_path", "data/corpus/processed/paragraphs.jsonl",
             "--index_dir", "/tmp/test_index"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        # In core env without [ml], this must exit 2
        try:
            import faiss  # noqa: F401
            from sentence_transformers import SentenceTransformer  # noqa: F401
            self.skipTest("ML deps are installed; cannot test missing-deps exit")
        except ImportError:
            pass
        self.assertEqual(result.returncode, 2, f"Expected exit 2, got {result.returncode}. stderr: {result.stderr}")
