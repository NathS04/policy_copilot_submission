"""
reproduce_online.py must fail preflight if dense index files are missing,
even when API key and ML deps are otherwise present.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestReproduceOnlineRequiresDenseIndex(unittest.TestCase):
    def test_exits_2_when_dense_index_missing(self):
        root = Path(__file__).resolve().parent.parent
        script = root / "scripts" / "reproduce_online.py"

        # Patch script root to a temp tree with no dense index.
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp)
            fake_scripts = fake_root / "scripts"
            fake_scripts.mkdir(parents=True, exist_ok=True)
            fake_script = fake_scripts / "reproduce_online.py"
            fake_script.write_text(script.read_text())

            env = os.environ.copy()
            env["OPENAI_API_KEY"] = "dummy"

            # If ML deps are missing on this machine, the ML preflight should trip first.
            # This test is specifically about index-missing preflight, so skip in that case.
            try:
                import faiss  # noqa: F401
                import torch  # noqa: F401
                from sentence_transformers import SentenceTransformer  # noqa: F401
            except ImportError:
                self.skipTest("ML deps are not installed; index-missing preflight branch not reachable")

            result = subprocess.run(
                [sys.executable, str(fake_script)],
                cwd=fake_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(result.returncode, 2, f"Expected exit 2, got {result.returncode}. stderr: {result.stderr}")
            self.assertIn("Dense index files are missing", result.stderr)


if __name__ == "__main__":
    unittest.main()

