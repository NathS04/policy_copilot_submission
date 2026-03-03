"""
Smoke test: verify_artifacts.py must exit with code 0 when no orphan artifacts exist.
"""
import subprocess
import sys
import unittest
from pathlib import Path


class TestVerifyArtifactsSmoke(unittest.TestCase):
    def test_verify_artifacts_exit_zero(self):
        root = Path(__file__).resolve().parent.parent
        # Ensure a make_figures-style manifest exists before verification.
        pre = subprocess.run(
            [sys.executable, "eval/analysis/make_figures.py",
             "--runs_dir", str(root / "results" / "runs"),
             "--out_fig_dir", str(root / "results" / "figures"),
             "--out_table_dir", str(root / "results" / "tables")],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if pre.returncode != 0:
            self.skipTest(f"make_figures pre-step failed: {pre.stderr[:500]}")

        result = subprocess.run(
            [sys.executable, "scripts/verify_artifacts.py"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"verify_artifacts must exit 0. stderr: {result.stderr}")
