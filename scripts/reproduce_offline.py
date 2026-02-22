"""
Offline reproduction script.
Runs the evaluation suite using:
- BM25 backend (no torch required)
- Extractive mode (no LLM keys required)
After running, verifies B2 and B3 outputs exist and contain non-empty paragraph_id in evidence.
Figures are generated in non-strict mode (B1 not required).
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd_list):
    if cmd_list[0] == "python":
        cmd_list[0] = sys.executable
    print(f"Running: {' '.join(cmd_list)}")
    try:
        subprocess.run(cmd_list, check=True, cwd=Path(__file__).resolve().parent.parent)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)


def main():
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    print("=== STARTING OFFLINE REPRODUCTION (BM25 / EXTRACTIVE) ===")
    os.environ["POLICY_COPILOT_BACKEND"] = "bm25"
    os.environ["MPLBACKEND"] = "Agg"  # headless figure generation

    run_command([
        sys.executable, "scripts/run_eval.py",
        "--baseline", "b2",
        "--split", "test",
        "--mode", "extractive",
        "--backend", "bm25",
        "--force",
    ])

    run_command([
        sys.executable, "scripts/run_eval.py",
        "--baseline", "b3",
        "--split", "test",
        "--mode", "extractive",
        "--backend", "bm25",
        "--force",
    ])

    results_dir = root / "results" / "runs"
    if not results_dir.exists() or not any(results_dir.iterdir()):
        print("ERROR: No results found in results/runs after execution.")
        sys.exit(1)

    # Require outputs.jsonl under *b2*test*extractive*bm25* and *b3*test*extractive*bm25*
    found_b2 = []
    found_b3 = []
    for run_path in results_dir.iterdir():
        if not run_path.is_dir():
            continue
        name = run_path.name.lower()
        if "b2" in name and "test" in name and "extractive" in name and "bm25" in name:
            found_b2.append(run_path)
        if "b3" in name and "test" in name and "extractive" in name and "bm25" in name:
            found_b3.append(run_path)

    outputs_b2 = None
    outputs_b3 = None
    for p in found_b2:
        f = p / "outputs.jsonl"
        if f.exists():
            outputs_b2 = f
            break
    for p in found_b3:
        f = p / "outputs.jsonl"
        if f.exists():
            outputs_b3 = f
            break

    if not outputs_b2 or not outputs_b3:
        print("ERROR: Required outputs not found.")
        print("  Need results/runs/*b2*test*extractive*bm25*/outputs.jsonl and *b3*test*extractive*bm25*/outputs.jsonl")
        sys.exit(1)

    NON_ANSWERS = {"INSUFFICIENT_EVIDENCE", "LLM_DISABLED", "ERROR"}

    def b2_ok(path):
        has_paragraph_id = False
        has_real_answer = False
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ids = obj.get("retrieved_paragraph_ids", [])
                    if ids and any(str(x).strip() for x in ids):
                        has_paragraph_id = True
                    ans = (obj.get("answer") or "").strip()
                    if ans and ans not in NON_ANSWERS:
                        has_real_answer = True
                except json.JSONDecodeError:
                    pass
        return has_paragraph_id and has_real_answer

    def b3_ok(path):
        has_paragraph_id = False
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ev = obj.get("evidence", [])
                    for e in ev:
                        pid = e.get("paragraph_id", "") if isinstance(e, dict) else str(e)
                        if pid:
                            has_paragraph_id = True
                            break
                    if not has_paragraph_id and obj.get("citations"):
                        has_paragraph_id = any(c for c in obj["citations"] if c)
                except (json.JSONDecodeError, TypeError):
                    pass
        return has_paragraph_id

    if not b2_ok(outputs_b2):
        print("ERROR: B2 outputs.jsonl must contain non-empty paragraph_id (retrieved_paragraph_ids) and at least one answerable record (answer != LLM_DISABLED).")
        sys.exit(1)
    if not b3_ok(outputs_b3):
        print("ERROR: B3 outputs.jsonl must contain at least one evidence entry with non-empty paragraph_id.")
        sys.exit(1)

    # Non-strict figure generation (no B1 in offline)
    print("=== GENERATING FIGURES (non-strict) ===")
    run_command([
        sys.executable, "eval/analysis/make_figures.py",
        "--runs_dir", str(root / "results" / "runs"),
        "--out_fig_dir", str(root / "results" / "figures"),
        "--out_table_dir", str(root / "results" / "tables"),
    ])

    print("=== OFFLINE REPRODUCTION COMPLETE ===")


if __name__ == "__main__":
    main()
