#!/usr/bin/env python3
"""
Build a clean examiner-facing submission ZIP using an explicit whitelist.

Output:
    Final_Submission_Nathaniel_Sebastian_201715051.zip
    (single top-level folder: policy_copilot_submission/)

The script stages whitelisted files into a temporary directory, validates the
result against a forbidden-path list, and writes the final ZIP next to the
project root. Anything not on the whitelist is excluded. Caches, venvs,
personal raw uploads, test-generated run folders, build backups, and AI chat
exports are all rejected.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT.parent
ZIP_NAME = "Final_Submission_Nathaniel_Sebastian_201715051.zip"
ZIP_PATH = BASE / ZIP_NAME
STAGE_PARENT = Path(tempfile.mkdtemp(prefix="policy_copilot_stage_"))
STAGE_DIR = STAGE_PARENT / "policy_copilot_submission"


# ---------------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------------

TOP_LEVEL_FILES = [
    ".env.example",
    ".gitignore",
    "CHANGELOG.md",
    "INSTRUCTIONS_FOR_EVALUATOR.md",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "requirements-ml.lock",
    "requirements.txt",
]

TOP_LEVEL_DIRS = [
    ".github",
    ".streamlit",
    "configs",
    "src",
    "tests",
]

SCRIPTS_INCLUDE = [
    "apply_leeds_template.py",
    "auto_label_gold.py",
    "build_audit_exports.py",
    "build_clean_submission_zip.py",
    "build_failure_taxonomy.py",
    "build_index.py",
    "build_report.py",
    "classify_errors.py",
    "compare_ablations.py",
    "compute_auditability_scores.py",
    "compute_human_eval.py",
    "docx_to_pdf_with_fields.py",
    "download_public_corpus.py",
    "eval_objective_slice.py",
    "export_human_eval_pack.py",
    "generate_corpus_pdf.py",
    "generate_diagrams.py",
    "import_human_eval_pack.py",
    "ingest_corpus.py",
    "ingest_public_corpus.py",
    "make_critic_dataset.py",
    "make_golden_set_template.py",
    "query_cli.py",
    "reproduce_all.sh",
    "reproduce_offline.py",
    "reproduce_online.py",
    "run_acceptance_tests.sh",
    "run_adversarial.py",
    "run_all_experiments.py",
    "run_critic_eval.py",
    "run_dev_tuning.sh",
    "run_eval.py",
    "run_transfer_eval.py",
    "select_best_config.py",
    "smoke_install.sh",
    "sweep_abstention.py",
    "validate_golden_set.py",
    "verify_artifacts.py",
    "verify_phase6.py",
]

DATA_INCLUDE = [
    "data/README.md",
    "data/handbook/internal_handbook_v1.md",
    "data/handbook/variants/critic_manifest.csv",
    "data/handbook/variants/manipulated/critic_snippets.jsonl",
    "data/handbook/variants/neutral/critic_snippets.jsonl",
    "data/licensing/sources_and_licenses.md",
    "data/corpus/manifests/corpus_manifest.csv",
    "data/corpus/processed/paragraphs.csv",
    "data/corpus/processed/paragraphs.jsonl",
    "data/public_transfer_corpus/README.md",
    "data/public_transfer_corpus/provenance.csv",
]

# Whole sub-trees we include as-is (filtered by the global exclusion pattern).
DATA_INCLUDE_TREES = [
    "data/public_transfer_corpus/processed",
    "data/public_transfer_corpus/raw",
]

EVAL_INCLUDE = [
    "eval/__init__.py",
    "eval/golden_set/golden_set.csv",
    "eval/golden_set/golden_set_README.md",
    "eval/golden_set/golden_set_frozen_v1.csv",
    "eval/golden_set/public_transfer_set.csv",
    "eval/metrics/__init__.py",
    "eval/metrics/abstention_metrics.py",
    "eval/metrics/citation_metrics.py",
    "eval/metrics/critic_metrics.py",
    "eval/metrics/retrieval_metrics.py",
    "eval/runners/run_all.py",
    "eval/runners/run_baselines.py",
    "eval/runners/run_full_system.py",
    "eval/analysis/__init__.py",
    "eval/analysis/error_taxonomy.md",
    "eval/analysis/make_figures.py",
    "eval/human_eval/README.md",
    "eval/human_eval/anonymised_scores.csv",
    "eval/human_eval/consent_text.md",
    "eval/human_eval/independent_review_results.csv",
    "eval/human_eval/per_category_results.csv",
    "eval/human_eval/per_query_raw.csv",
    "eval/human_eval/rubric.md",
    "eval/human_eval/summary_stats.csv",
    "eval/human_eval/thematic_codes.csv",
    "eval/human_eval/thematic_summary.md",
    "eval/public_transfer/README.md",
    "eval/public_transfer/failure_taxonomy.csv",
    "eval/adversarial/README.md",
    "eval/adversarial/adversarial_queries.csv",
    "eval/adversarial/adversarial_results_extractive.csv",
    "eval/adversarial/adversarial_results_generative.csv",
    "eval/adversarial/adversarial_summary.csv",
    "eval/rubrics/auditability_rubric.md",
    "eval/rubrics/critic_rubric.md",
    "eval/rubrics/groundedness_rubric.md",
    "eval/rubrics/usefulness_rubric.md",
]

RESULTS_INCLUDE = [
    "results/manifest.json",
    "results/figures/fig_baselines.png",
    "results/figures/fig_groundedness.png",
    "results/figures/fig_retrieval.png",
    "results/figures/fig_tradeoff.png",
    "results/tables/ablation_comparison.csv",
    "results/tables/auditability_scores.csv",
    "results/tables/failure_taxonomy.csv",
    "results/tables/objective_slice_results.csv",
    "results/tables/run_summary.csv",
    "results/tables/threshold_sweep.csv",
]

# Whole canonical run folders.
RESULTS_RUNS = [
    "results/runs/b1_generative_final",
    "results/runs/b2_generative_bm25_fallback_final",
    "results/runs/b3_generative_bm25_fallback_final",
    "results/runs/b3_extractive_public_transfer",
]

DOCS_INCLUDE = [
    "docs/claim_evidence_map.md",
    "docs/demo_scripts.md",
    "docs/figure_table_register.md",
    "docs/final_submission_checklist.md",
    "docs/phase7_acceptance_tests.md",
    "docs/project_truth_registry.md",
    "docs/reference_audit.md",
    "docs/reproducibility_checklist.md",
    "docs/requirements_traceability_matrix.md",
    "docs/risk_audit_table.md",
    "docs/sprints.md",
    "docs/ui_architecture.md",
    "docs/ui_scope.md",
    "docs/evidence/README.md",
    "docs/evidence/capture_guide.md",
    "docs/evidence/checklist.md",
    "docs/evidence/human_eval/README.md",
    "docs/evidence/human_eval/anonymised_scores.csv",
    "docs/evidence/human_eval/consent_text.md",
    "docs/evidence/human_eval/inter_rater_agreement.md",
    "docs/evidence/human_eval/participant_info.md",
    "docs/evidence/human_eval/per_query_anonymised_scores.csv",
    "docs/evidence/human_eval/per_query_summary_stats.csv",
    "docs/evidence/human_eval/rubric.md",
    "docs/evidence/human_eval/summary_stats.csv",
    "docs/evidence/human_eval/thematic_summary.md",
    "docs/evidence/verification/adversarial_test_summary.md",
    "docs/evidence/verification/audit_export_answerable.md",
    "docs/evidence/verification/audit_export_contradiction.md",
    "docs/evidence/verification/audit_export_index.md",
    "docs/evidence/verification/audit_export_unanswerable.md",
    "docs/evidence/verification/public_transfer_failure_taxonomy.md",
    "docs/meetings/000_template.md",
    "docs/meetings/01_project_kickoff.md",
    "docs/meetings/02_corpus_and_retrieval.md",
    "docs/meetings/03_reliability_layer.md",
    "docs/meetings/04_evaluation_harness.md",
    "docs/meetings/05_ui_and_packaging.md",
    "docs/meetings/06_final_review.md",
    "docs/research/citation_chain_c6_c10.md",
    "docs/research/citation_chain_clusters_1_4.md",
    "docs/research/comparator_matrix.md",
    "docs/research/dissertation_benchmark_report.md",
    "docs/research/gap_statement.md",
    "docs/research/literature_matrix.md",
    "docs/research/report_mapping.md",
    "docs/research/search_strategy.md",
    "docs/research/taxonomy_of_related_work.md",
    "docs/report/Final_Report_Nathaniel_Sebastian_201715051.md",
    "docs/report/Final_Report_Nathaniel_Sebastian_201715051.pdf",
    "docs/report/report_style.css",
    "docs/report/build_assets/Final_Report_Template.docx",
    "docs/report/build_assets/leeds_template.docx",
]

DOCS_INCLUDE_TREES = [
    "docs/report/figures",
]


# ---------------------------------------------------------------------------
# Forbidden patterns (validated post-build)
# ---------------------------------------------------------------------------

FORBIDDEN_SUBSTRINGS = [
    "/.git/",
    "/.claude/",
    "/.pytest_cache/",
    "/.ruff_cache/",
    "/.mypy_cache/",
    "/__pycache__/",
    "/__MACOSX/",
    "/.DS_Store",
    "/Helper/",
    "Helper.zip",
    "/_AI_ARTIFACTS/",
    "PHASE6_PATCH_OUTPUT.md",
    "results/runs/_archive/",
    "results/runs/test_",
    "data/corpus/raw/uploads/",
    "CV_",
    "Tenancy agreement",
    "Final_Report_Draft.pdf",
    "Final_Report_Draft.md",
    ".venv_seal/",
    ".venv/",
    ".venv312/",
    "voice_review_notes.md",
]

FORBIDDEN_ENDSWITH = [
    ".env",  # but .env.example allowed (handled explicitly)
    ".pyc",
    ".pyo",
    ".egg-info",
]

# Files we always exclude when walking a directory tree.
TREE_IGNORE_PATTERNS = (
    ".git",
    ".github",  # we copy .github manually with workflows only
    ".claude",
    ".venv",
    ".venv_seal",
    ".venv312",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "__pycache__",
    "__MACOSX",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    "_archive",
    "Helper",
    "Helper.zip",
    "_AI_ARTIFACTS",
    "PHASE6_PATCH_OUTPUT.md",
    "*.bak",
    "voice_review_notes.md",
    "forms",  # eval/human_eval/forms — internal collection artefacts
    "packs",  # eval/human_eval/packs — export bundles
)


# ---------------------------------------------------------------------------
# Stage builders
# ---------------------------------------------------------------------------

def stage_file(rel_path: str, missing: list[str]) -> int:
    src = ROOT / rel_path
    if not src.is_file():
        missing.append(rel_path)
        return 0
    dst = STAGE_DIR / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return 1


def stage_tree(rel_path: str, missing: list[str]) -> int:
    src = ROOT / rel_path
    if not src.is_dir():
        missing.append(rel_path)
        return 0
    dst = STAGE_DIR / rel_path
    if dst.exists():
        return 0  # already copied (e.g. nested whitelist)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(*TREE_IGNORE_PATTERNS),
    )
    return sum(1 for _ in dst.rglob("*") if _.is_file())


def stage_github_workflows() -> int:
    """Copy only .github/workflows/, not the rest of .github."""
    src = ROOT / ".github" / "workflows"
    if not src.is_dir():
        return 0
    dst = STAGE_DIR / ".github" / "workflows"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*TREE_IGNORE_PATTERNS))
    return sum(1 for _ in dst.rglob("*") if _.is_file())


def stage_scripts() -> tuple[int, list[str]]:
    src_dir = ROOT / "scripts"
    dst_dir = STAGE_DIR / "scripts"
    dst_dir.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []
    count = 0
    for name in SCRIPTS_INCLUDE:
        src = src_dir / name
        if not src.is_file():
            missing.append(f"scripts/{name}")
            continue
        shutil.copy2(src, dst_dir / name)
        count += 1
    return count, missing


def build_stage() -> tuple[int, list[str]]:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    total = 0

    # Top-level files
    for f in TOP_LEVEL_FILES:
        total += stage_file(f, missing)

    # Top-level dirs (filtered)
    for d in TOP_LEVEL_DIRS:
        if d == ".github":
            continue  # handled separately
        total += stage_tree(d, missing)
    total += stage_github_workflows()

    # Scripts (selective)
    s_count, s_missing = stage_scripts()
    total += s_count
    missing.extend(s_missing)

    # Data files + trees
    for f in DATA_INCLUDE:
        total += stage_file(f, missing)
    for d in DATA_INCLUDE_TREES:
        total += stage_tree(d, missing)

    # Eval files
    for f in EVAL_INCLUDE:
        total += stage_file(f, missing)

    # Results files + canonical run folders
    for f in RESULTS_INCLUDE:
        total += stage_file(f, missing)
    for d in RESULTS_RUNS:
        total += stage_tree(d, missing)

    # Docs files + trees
    for f in DOCS_INCLUDE:
        total += stage_file(f, missing)
    for d in DOCS_INCLUDE_TREES:
        total += stage_tree(d, missing)

    return total, missing


# ---------------------------------------------------------------------------
# ZIP build + validation
# ---------------------------------------------------------------------------

def zip_stage() -> int:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    file_count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(STAGE_DIR.rglob("*")):
            if f.is_file():
                arc = f.relative_to(STAGE_DIR.parent).as_posix()
                zf.write(f, arc)
                file_count += 1
    return file_count


def validate_zip() -> tuple[list[str], set[str]]:
    """Open the ZIP and check for forbidden paths. Returns (bad_paths, top_levels)."""
    bad: list[str] = []
    with zipfile.ZipFile(ZIP_PATH) as z:
        names = z.namelist()
    for n in names:
        # Allow .env.example (explicit exception)
        if n.endswith("/.env.example") or n.endswith(".env.example"):
            continue
        for sub in FORBIDDEN_SUBSTRINGS:
            if sub in n:
                bad.append(n)
                break
        else:
            for suf in FORBIDDEN_ENDSWITH:
                if n.endswith(suf):
                    bad.append(n)
                    break
    top_levels = {n.split("/", 1)[0] for n in names if n.strip()}
    return bad, top_levels


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"Staging into: {STAGE_DIR}")
    total_staged, missing = build_stage()
    print(f"Staged {total_staged} files.")
    if missing:
        print(f"WARNING: {len(missing)} whitelisted path(s) missing on disk:")
        for m in missing[:20]:
            print(f"  - {m}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")

    file_count = zip_stage()
    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    bad, top_levels = validate_zip()

    print()
    print("=" * 60)
    print(f"ZIP path:    {ZIP_PATH}")
    print(f"ZIP size:    {size_mb:.2f} MB")
    print(f"Files in ZIP: {file_count}")
    print(f"Top-level folders: {sorted(top_levels)}")

    failed = False
    if top_levels != {"policy_copilot_submission"}:
        print(f"FAIL: top-level folders must be exactly {{'policy_copilot_submission'}}")
        failed = True

    if bad:
        print(f"FAIL: {len(bad)} forbidden path(s) found:")
        for b in sorted(set(bad))[:30]:
            print(f"  - {b}")
        failed = True
    else:
        print("Forbidden-path scan: PASSED")

    # Cleanup staging directory.
    if STAGE_PARENT.exists():
        shutil.rmtree(STAGE_PARENT)

    if failed:
        # Remove the bad ZIP so it can't be shipped accidentally.
        if ZIP_PATH.exists():
            ZIP_PATH.unlink()
        print("\nZIP rejected and deleted.")
        return 1
    print("\nZIP accepted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
