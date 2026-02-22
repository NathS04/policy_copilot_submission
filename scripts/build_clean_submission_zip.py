#!/usr/bin/env python3
"""
Build a clean final-submission zip containing only what evaluators need.
Excludes: Helper/, _AI_ARTIFACTS/, PHASE6_PATCH_OUTPUT.md, results/, .git, venvs, caches.
"""
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT.parent
ZIP_PATH = BASE / "policy_copilot_submission.zip"
STAGE_DIR = BASE / "policy_copilot_submission"

# Top-level items to INCLUDE in submission
INCLUDE_NAMES = {
    ".env.example",
    ".gitignore",
    "README.md",
    "INSTRUCTIONS_FOR_EVALUATOR.md",
    "INSTRUCTIONS_FOR_GPT.md",
    "pyproject.toml",
    "requirements.txt",
    "requirements-ml.lock",
    "configs",
    "data",
    "docs",
    "eval",
    "scripts",
    "src",
    "tests",
}

# Exclude from any directory when copying
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    ".venv312",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "__pycache__",
    ".DS_Store",
}


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(".")


def build_stage():
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    for name in INCLUDE_NAMES:
        src = ROOT / name
        if not src.exists():
            continue
        dst = STAGE_DIR / name
        if src.is_dir():
            shutil.copytree(
                src,
                dst,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".venv",
                    ".venv312",
                    ".pytest_cache",
                    ".ruff_cache",
                    ".mypy_cache",
                    "__pycache__",
                    "*.pyc",
                    "*.pyo",
                    ".DS_Store",
                ),
                dirs_exist_ok=False,
            )
        else:
            shutil.copy2(src, dst)


def zip_stage():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(STAGE_DIR.rglob("*")):
            if f.is_file():
                arc = f.relative_to(BASE).as_posix()
                zf.write(f, arc)


def main():
    build_stage()
    zip_stage()
    print("Wrote:", ZIP_PATH)
    print("Size:", ZIP_PATH.stat().st_size)
    # Cleanup stage
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)


if __name__ == "__main__":
    main()
