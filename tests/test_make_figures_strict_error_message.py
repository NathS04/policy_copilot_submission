"""
make_figures.py --strict must exit 1 and print a clear message
listing which runs are missing (at least b1/test in offline mode).
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestMakeFiguresStrictErrorMessage(unittest.TestCase):
    def test_strict_exits_1_with_missing_b1(self):
        root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env.setdefault("MPLBACKEND", "Agg")
        result = subprocess.run(
            [sys.executable, "eval/analysis/make_figures.py", "--strict"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # In offline-only mode, b1 runs won't exist, so strict must fail
        try:
            # If b1 test runs exist (online mode), this test is N/A
            runs_dir = root / "results" / "runs"
            has_b1_test = any(
                "b1" in p.name and "test" in p.name
                for p in runs_dir.iterdir() if p.is_dir()
            ) if runs_dir.exists() else False
            if has_b1_test:
                self.skipTest("b1/test run exists; strict will pass (online mode)")
        except Exception:
            pass

        self.assertEqual(result.returncode, 1, f"Expected exit 1. stdout: {result.stdout[-500:]}")
        combined = result.stdout + result.stderr
        self.assertIn("requires runs that are missing", combined)
        self.assertIn("b1", combined)
