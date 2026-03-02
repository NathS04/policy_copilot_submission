#!/usr/bin/env python3
"""
Run the full Phase 6 acceptance checklist (steps 1-9).

This mirrors INSTRUCTIONS_FOR_GPT.md and exits non-zero on any failure.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
VENV_BIN = ROOT / ".venv" / "bin"


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{VENV_BIN}:{env.get('PATH', '')}"
    return env


def _run(cmd: list[str], step_name: str, expect_exit: int = 0, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"=== {step_name} ===")
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        env=_subprocess_env(),
    )
    if capture:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    if result.returncode != expect_exit:
        print(
            f"ERROR: {step_name} failed (expected exit {expect_exit}, got {result.returncode}).",
            file=sys.stderr,
        )
        print(f"Command: {' '.join(cmd)}", file=sys.stderr)
        sys.exit(result.returncode if result.returncode != 0 else 1)
    return result


def _require_glob(pattern: str, message: str) -> list[str]:
    matches = sorted(glob.glob(pattern))
    if not matches:
        print(f"ERROR: {message}", file=sys.stderr)
        print(f"Pattern: {pattern}", file=sys.stderr)
        sys.exit(1)
    for match in matches:
        print(match)
    return matches


def _step6_b2_quality_check(b2_outputs_path: str) -> None:
    bad = 0
    good = 0
    with open(b2_outputs_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            if row.get("is_answerable") is True:
                answer = row.get("answer")
                if answer == "LLM_DISABLED":
                    bad += 1
                elif answer not in ("INSUFFICIENT_EVIDENCE", "ERROR", None):
                    good += 1

    print("answerable_good", good, "answerable_bad_LLM_DISABLED", bad, "file", b2_outputs_path)
    if bad != 0:
        print("ERROR: B2 still emits LLM_DISABLED for answerable queries.", file=sys.stderr)
        sys.exit(1)
    if good <= 0:
        print("ERROR: B2 produced no real answers.", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    # 1) Clean core install
    _run([sys.executable, "-m", "venv", str(ROOT / ".venv")], "1) Clean core install (NO ML)")
    _run([str(VENV_PYTHON), "-m", "pip", "install", "-U", "pip", "-q"], "Upgrade pip")
    _run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".", "-q"], "Install core package")
    _run([str(VENV_PYTHON), "-c", "import policy_copilot; print('import ok')"], "Verify import")

    # 2) Dev deps + tests
    _run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[dev]", "-q"], "2) Install dev dependencies")
    _run([str(VENV_PYTHON), "-m", "pytest", "-q"], "Run test suite")

    # 3) CLI help
    _run([str(VENV_PYTHON), "scripts/run_eval.py", "--help"], "3) run_eval CLI help")
    _run([str(VENV_PYTHON), "scripts/build_index.py", "--help"], "3) build_index CLI help")

    # 4) Offline reproduction
    _run([str(VENV_PYTHON), "scripts/reproduce_offline.py"], "4) Offline reproduction (no keys, no torch)")

    # 5) B2/B3 outputs exist
    b2_pattern = str(ROOT / "results" / "runs" / "*b2*test*extractive*bm25*" / "outputs.jsonl")
    b3_pattern = str(ROOT / "results" / "runs" / "*b3*test*extractive*bm25*" / "outputs.jsonl")
    b2_paths = _require_glob(b2_pattern, "Missing B2 outputs.jsonl.")
    _require_glob(b3_pattern, "Missing B3 outputs.jsonl.")

    # 6) B2 should not emit LLM_DISABLED for answerable
    _step6_b2_quality_check(b2_paths[-1])

    # 7) Strict figures must fail
    strict_result = _run(
        [str(VENV_PYTHON), "eval/analysis/make_figures.py", "--strict"],
        "7) Strict figures must fail",
        expect_exit=1,
        capture=True,
    )
    combined = f"{strict_result.stdout}\n{strict_result.stderr}"
    if "STRICT ERROR" not in combined:
        print("ERROR: strict mode failed, but not with a strict missing-runs error.", file=sys.stderr)
        return 1
    print("Strict correctly failed (exit 1).")

    # 8) Non-strict figures must succeed
    _run(
        [
            str(VENV_PYTHON),
            "eval/analysis/make_figures.py",
            "--out_fig_dir",
            "results/figures",
            "--out_table_dir",
            "results/tables",
        ],
        "8) Non-strict figures must succeed",
    )

    # 9) Artifact verification
    _run([str(VENV_PYTHON), "scripts/verify_artifacts.py"], "9) Artifact verification")

    print("=== All acceptance tests passed. ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
