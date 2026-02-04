"""
Online reproduction script.
Runs the FULL evaluation suite using:
- Dense backend (FAISS + SentenceTransformers)
- Generative mode (requires LLM keys)
- All baselines (B1, B2, B3) on dev + test splits
- B3 ablations (no_rerank, no_verify, no_contradictions) on test
- Strict figure generation (figures to results/figures, tables to results/tables)

Pre-flight: exits immediately with code 2 if API key or ML deps are missing.
"""
import os
import subprocess
import sys
from pathlib import Path


def _missing_dense_index_files(root: Path) -> list[Path]:
    """Return required dense-index files that are missing."""
    index_dir = root / "data" / "corpus" / "processed" / "index"
    required = ["faiss.index", "docstore.jsonl", "index_meta.json"]
    missing = [(index_dir / name) for name in required if not (index_dir / name).exists()]
    return missing


def _preflight(root: Path):
    """Fail fast if prerequisites are missing. Must not create any run dirs."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        print("ERROR: OPENAI_API_KEY not set. Online reproduction requires an API key.", file=sys.stderr)
        sys.exit(2)
    try:
        import faiss  # noqa: F401
        from sentence_transformers import SentenceTransformer  # noqa: F401
        import torch  # noqa: F401
    except ImportError as e:
        print(f"ERROR: Dense reproduction requires ML extras. Run: pip install -e \".[ml]\"\n  (missing: {e})", file=sys.stderr)
        sys.exit(2)

    missing = _missing_dense_index_files(root)
    if missing:
        missing_str = ", ".join(str(p) for p in missing)
        print(
            "ERROR: Dense index files are missing. "
            f"Missing: {missing_str}\n"
            "Build the dense index first with: python scripts/build_index.py",
            file=sys.stderr,
        )
        sys.exit(2)

    # Sanity-load index to prevent silent fallback from a corrupt/invalid dense index.
    try:
        from policy_copilot.index.faiss_index import FaissIndex

        index = FaissIndex()
        index.load(root / "data" / "corpus" / "processed" / "index")
    except Exception as e:
        print(
            "ERROR: Dense index is present but failed to load. "
            "Rebuild it with: python scripts/build_index.py\n"
            f"  (load error: {e})",
            file=sys.stderr,
        )
        sys.exit(2)


def run_command(cmd_list, cwd=None):
    if cmd_list[0] == "python":
        cmd_list[0] = sys.executable
    print(f"Running: {' '.join(cmd_list)}")
    try:
        subprocess.run(cmd_list, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)


def main():
    root = Path(__file__).resolve().parent.parent
    _preflight(root)
    os.chdir(root)

    print("=== STARTING ONLINE REPRODUCTION (DENSE / GENERATIVE) ===")
    os.environ.setdefault("MPLBACKEND", "Agg")

    # 1. Baselines on dev + test (separate runs so b1_test_* exists for strict figures)
    for split in ("dev", "test"):
        run_command([
            "python", "scripts/run_eval.py",
            "--baseline", "b1",
            "--split", split,
            "--mode", "generative",
            "--backend", "dense",
            "--force",
        ], cwd=root)
        run_command([
            "python", "scripts/run_eval.py",
            "--baseline", "b2",
            "--split", split,
            "--mode", "generative",
            "--backend", "dense",
            "--force",
        ], cwd=root)
        run_command([
            "python", "scripts/run_eval.py",
            "--baseline", "b3",
            "--split", split,
            "--mode", "generative",
            "--backend", "dense",
            "--force",
        ], cwd=root)

    # 2. Ablations (B3 variants) on test
    run_command([
        "python", "scripts/run_eval.py", "--baseline", "b3", "--split", "test",
        "--mode", "generative", "--backend", "dense",
        "--no_rerank", "--run_name", "b3_no_rerank", "--force",
    ], cwd=root)
    run_command([
        "python", "scripts/run_eval.py", "--baseline", "b3", "--split", "test",
        "--mode", "generative", "--backend", "dense",
        "--no_verify", "--run_name", "b3_no_verify", "--force",
    ], cwd=root)
    run_command([
        "python", "scripts/run_eval.py", "--baseline", "b3", "--split", "test",
        "--mode", "generative", "--backend", "dense",
        "--no_contradictions", "--run_name", "b3_no_contradictions", "--force",
    ], cwd=root)

    # 3. Strict figures
    print("=== GENERATING FIGURES (STRICT) ===")
    run_command([
        "python", "eval/analysis/make_figures.py", "--strict",
        "--runs_dir", str(root / "results" / "runs"),
        "--out_fig_dir", str(root / "results" / "figures"),
        "--out_table_dir", str(root / "results" / "tables"),
    ], cwd=root)

    print("=== ONLINE REPRODUCTION COMPLETE ===")


if __name__ == "__main__":
    main()
