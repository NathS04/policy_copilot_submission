"""
run_eval.py in generative mode must exit(2) when no API key is set,
unless --allow_no_key is passed.
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path
import json


class TestRunEvalRequiresKeyInGenerative(unittest.TestCase):
    def test_generative_no_key_exits_2(self):
        root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        result = subprocess.run(
            [sys.executable, "scripts/run_eval.py",
             "--baseline", "b1", "--split", "test", "--mode", "generative",
             "--backend", "bm25"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 2, f"Expected exit 2. stderr: {result.stderr}")
        self.assertIn("GENERATIVE mode requires an API key", result.stderr)

    def test_allow_no_key_runs(self):
        root = Path(__file__).resolve().parent.parent
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        env["POLICY_COPILOT_BACKEND"] = "bm25"
        run_name = "test_allow_no_key_generates_llm_disabled"
        result = subprocess.run(
            [sys.executable, "scripts/run_eval.py",
             "--baseline", "b2", "--split", "test", "--mode", "generative",
             "--backend", "bm25", "--run_name", run_name, "--allow_no_key", "--force"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, f"Expected exit 0. stderr: {result.stderr[-500:]}")
        outputs_path = root / "results" / "runs" / run_name / "outputs.jsonl"
        self.assertTrue(outputs_path.exists(), f"Expected outputs at {outputs_path}")
        found = False
        with open(outputs_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if obj.get("answer") == "LLM_DISABLED":
                    found = True
                    break
        self.assertTrue(found, "Expected at least one output record with answer='LLM_DISABLED' when --allow_no_key is used")
