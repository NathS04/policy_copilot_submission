"""
reproduce_online.py must exit(2) immediately when OPENAI_API_KEY is missing,
and must NOT create any run directories.
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestReproduceOnlinePreflight(unittest.TestCase):
    def test_exits_2_without_api_key(self):
        root = Path(__file__).resolve().parent.parent
        runs_before = set()
        runs_dir = root / "results" / "runs"
        if runs_dir.exists():
            runs_before = {p.name for p in runs_dir.iterdir() if p.is_dir()}

        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        result = subprocess.run(
            [sys.executable, "scripts/reproduce_online.py"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 2, f"Expected exit 2, got {result.returncode}. stderr: {result.stderr}")
        self.assertIn("OPENAI_API_KEY", result.stderr)

        runs_after = set()
        if runs_dir.exists():
            runs_after = {p.name for p in runs_dir.iterdir() if p.is_dir()}
        new_runs = runs_after - runs_before
        self.assertEqual(len(new_runs), 0, f"Preflight must not create runs, but created: {new_runs}")

    def test_exits_2_with_dummy_key_but_missing_ml_deps(self):
        root = Path(__file__).resolve().parent.parent
        runs_before = set()
        runs_dir = root / "results" / "runs"
        if runs_dir.exists():
            runs_before = {p.name for p in runs_dir.iterdir() if p.is_dir()}

        # If ML deps are installed, this case is not applicable.
        try:
            import faiss  # noqa: F401
            import torch  # noqa: F401
            from sentence_transformers import SentenceTransformer  # noqa: F401
            self.skipTest("ML deps are installed; missing-ML preflight case is not applicable")
        except ImportError:
            pass

        env = os.environ.copy()
        env["OPENAI_API_KEY"] = "dummy"
        env.pop("ANTHROPIC_API_KEY", None)
        result = subprocess.run(
            [sys.executable, "scripts/reproduce_online.py"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 2, f"Expected exit 2, got {result.returncode}. stderr: {result.stderr}")
        self.assertIn("pip install -e", result.stderr)

        runs_after = set()
        if runs_dir.exists():
            runs_after = {p.name for p in runs_dir.iterdir() if p.is_dir()}
        new_runs = runs_after - runs_before
        self.assertEqual(len(new_runs), 0, f"Preflight must not create runs, but created: {new_runs}")
