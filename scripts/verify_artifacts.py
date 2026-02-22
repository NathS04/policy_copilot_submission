"""
Verify that results artifacts are regenerable and provenance is honest.

Checks:
- Build a run manifest from results/runs with config+summary hashes.
- Ensure files in results/figures and results/tables match make_figures outputs.
- Fail on orphan artifacts.
- In --strict mode, fail on backend_requested/backend_used mismatches unless explicitly allowed.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_FIGURES = {"fig_baselines.png", "fig_retrieval.png", "fig_groundedness.png", "fig_tradeoff.png"}
ALLOWED_TABLES = {"run_summary.csv"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _list_regular_files(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted([p.name for p in path.iterdir() if p.is_file()])


def main():
    parser = argparse.ArgumentParser(description="Verify artifact integrity.")
    parser.add_argument("--strict", action="store_true",
                        help="Treat backend fallback (requested!=used) as fatal.")
    parser.add_argument("--allow_backend_mismatch", action="store_true",
                        help="Allow backend_requested!=backend_used even in strict mode.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    runs_dir = root / "results" / "runs"
    fig_dir = root / "results" / "figures"
    table_dir = root / "results" / "tables"
    manifest_path = root / "results" / "manifest.json"

    errors = []
    warnings = []
    run_ids = []
    run_hashes = {}

    # 1) Scan runs and build hash manifest
    if runs_dir.exists():
        for p in sorted(runs_dir.iterdir()):
            if not p.is_dir():
                continue
            cfg_path = p / "run_config.json"
            summary_path = p / "summary.json"
            if not cfg_path.exists() or not summary_path.exists():
                continue
            try:
                with open(cfg_path) as f:
                    cfg = json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid run_config.json in {p.name}: {e}")
                continue

            b_req = cfg.get("backend_requested", cfg.get("backend"))
            b_used = cfg.get("backend_used", cfg.get("backend"))
            if b_req and b_used and b_req != b_used:
                msg = f"Run {p.name}: backend_requested={b_req} but backend_used={b_used}"
                if args.strict and not args.allow_backend_mismatch:
                    errors.append(msg)
                else:
                    warnings.append(msg)

            run_ids.append(p.name)
            run_hashes[p.name] = {
                "run_config_sha256": _sha256_file(cfg_path),
                "summary_sha256": _sha256_file(summary_path),
                "baseline": cfg.get("baseline"),
                "split": cfg.get("split"),
                "mode": cfg.get("mode"),
                "backend_requested": b_req,
                "backend_used": b_used,
            }
    else:
        warnings.append(f"Runs directory not found: {runs_dir}")

    if run_ids:
        print(f"Runs used for artifacts: {run_ids}")
    else:
        print("No complete runs (run_config.json + summary.json) found in results/runs.")

    # 2) Load existing make_figures manifest (if present)
    declared_manifest = _load_json(manifest_path)
    declared_source = declared_manifest.get("source", "")
    expected_figures = set(declared_manifest.get("figures", []))
    expected_tables = set(declared_manifest.get("tables", []))
    expected_runs = set(declared_manifest.get("runs", []))

    if declared_manifest and declared_source != "make_figures.py":
        warnings.append(
            f"{manifest_path} source is '{declared_source}', expected 'make_figures.py'. "
            "Regenerate with eval/analysis/make_figures.py."
        )

    # 3) Check figures and tables for orphan files
    all_figure_files = _list_regular_files(fig_dir)
    all_table_files = _list_regular_files(table_dir)
    actual_figures = [name for name in all_figure_files if name.lower().endswith(".png")]
    actual_tables = [name for name in all_table_files if name.lower().endswith(".csv")]

    for name in all_figure_files:
        if not name.lower().endswith(".png"):
            errors.append(f"Orphan figure artifact (unexpected type): results/figures/{name}")
    for name in all_table_files:
        if not name.lower().endswith(".csv"):
            errors.append(f"Orphan table artifact (unexpected type): results/tables/{name}")

    for name in actual_figures:
        if name not in ALLOWED_FIGURES:
            errors.append(
                f"Orphan figure: {name} (make_figures.py only generates {sorted(ALLOWED_FIGURES)})."
            )
        if expected_figures and name not in expected_figures:
            errors.append(f"Orphan figure not listed in manifest: results/figures/{name}")
        else:
            print(f"Figure {name} present.")

    for name in actual_tables:
        if name not in ALLOWED_TABLES:
            errors.append(
                f"Orphan table: {name} (make_figures.py only generates {sorted(ALLOWED_TABLES)})."
            )
        if expected_tables and name not in expected_tables:
            errors.append(f"Orphan table not listed in manifest: results/tables/{name}")
        else:
            print(f"Table {name} present.")

    # If a make_figures manifest exists, required artifacts listed there must exist.
    for name in sorted(expected_figures):
        if name not in actual_figures:
            errors.append(f"Manifest-declared figure missing on disk: results/figures/{name}")
    for name in sorted(expected_tables):
        if name not in actual_tables:
            errors.append(f"Manifest-declared table missing on disk: results/tables/{name}")

    # If a make_figures manifest exists, listed runs should still exist.
    if expected_runs:
        missing_runs = sorted(expected_runs - set(run_ids))
        if missing_runs:
            errors.append(f"Manifest references missing runs: {missing_runs}")

    # 4) Write verification manifest (retains make_figures source identity)
    verification_manifest = {
        "source": "make_figures.py",
        "verified_by": "verify_artifacts.py",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "strict": args.strict,
        "allow_backend_mismatch": args.allow_backend_mismatch,
        "runs": run_ids,
        "run_hashes": run_hashes,
        "figures": actual_figures,
        "tables": actual_tables,
    }
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(verification_manifest, f, indent=2)
    print(f"Wrote {manifest_path}")

    # 5) Emit warnings and decide status
    for w in warnings:
        print(f"WARNING: {w}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print("Artifact verification passed.")


if __name__ == "__main__":
    main()
