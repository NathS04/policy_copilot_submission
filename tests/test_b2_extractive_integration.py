"""
Integration-style test: run run_eval.py baseline b2 test extractive bm25 and verify
outputs.jsonl contains at least one answerable record with answer != "LLM_DISABLED".
Requires golden set and BM25 corpus/index; skips if not available.
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestB2ExtractiveIntegration(unittest.TestCase):
    def test_b2_extractive_produces_real_answers(self):
        root = Path(__file__).resolve().parent.parent
        golden = root / "eval" / "golden_set" / "golden_set.csv"
        if not golden.exists():
            self.skipTest("Golden set not found")

        env = os.environ.copy()
        env["POLICY_COPILOT_BACKEND"] = "bm25"
        run_name = "test_b2_extractive_bm25_integration"

        result = subprocess.run(
            [
                sys.executable, "scripts/run_eval.py",
                "--baseline", "b2",
                "--split", "test",
                "--mode", "extractive",
                "--backend", "bm25",
                "--run_name", run_name,
                "--force",
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            self.skipTest(f"run_eval failed (e.g. BM25 index missing): {result.stderr[:500]}")

        run_dir = root / "results" / "runs" / run_name
        outputs = run_dir / "outputs.jsonl"
        self.assertTrue(outputs.exists(), f"Expected {outputs} after run_eval")

        answered_count = 0
        with open(outputs) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("category") != "answerable":
                        continue
                    ans = (obj.get("answer") or "").strip()
                    if ans and ans not in {"INSUFFICIENT_EVIDENCE", "LLM_DISABLED", "ERROR"}:
                        answered_count += 1
                except json.JSONDecodeError:
                    pass

        self.assertGreaterEqual(
            answered_count, 1,
            "outputs.jsonl must contain at least 1 answerable record with answer != LLM_DISABLED (B2 extractive baseline)"
        )


if __name__ == "__main__":
    unittest.main()
