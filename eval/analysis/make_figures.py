"""
Generates four definitive figures for the dissertation.
Strict mode enforces presence of required runs; fails with explicit missing list.
Honest plotting: no silent 0.0 defaults for missing metrics (use NaN/N/A).
Writes to results/figures/*.png and results/tables/*.csv.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Use matplotlib-only styling so core install stays lightweight.
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")
PALETTE = {"b1": "#4e79a7", "b2": "#f28e2b", "b3": "#e15759"}  # Tableau 10

REQUIRED_RUNS = {
    "fig_baselines": [
        {"baseline": "b1", "split": "test"},
        {"baseline": "b2", "split": "test"},
        {"baseline": "b3", "split": "test"},
    ],
    "fig_retrieval": [
        {"baseline": "b2", "split": "test"},
        {"baseline": "b3", "split": "test"},
    ],
    "fig_groundedness": [
        {"baseline": "b3", "split": "test"},
    ],
    "fig_tradeoff": [
        {"baseline": "b3", "split": "test"},
    ],
}


def _variant_color(variant: str, idx: int) -> str:
    if variant in PALETTE:
        return PALETTE[variant]
    if variant.startswith("b1"):
        return PALETTE["b1"]
    if variant.startswith("b2"):
        return PALETTE["b2"]
    if variant.startswith("b3"):
        return PALETTE["b3"]
    cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["#4e79a7"])
    return cycle[idx % len(cycle)]


def _plot_grouped_metrics(ax, plot_df: pd.DataFrame, metrics: list[str], variants: list[str]):
    """Grouped bar chart with mean aggregation per variant/metric."""
    x = np.arange(len(metrics), dtype=float)
    width = 0.8 / max(1, len(variants))

    for idx, variant in enumerate(variants):
        sub = plot_df[plot_df["variant"] == variant]
        values = []
        for metric in metrics:
            series = sub[metric].dropna()
            values.append(float(series.mean()) if not series.empty else np.nan)

        offset = (idx - (len(variants) - 1) / 2.0) * width
        ax.bar(
            x + offset,
            values,
            width=width,
            label=variant,
            color=_variant_color(variant, idx),
        )

    ax.set_xticks(x)
    ax.set_xticklabels(metrics)


def load_run_data(runs_dir: Path, strict: bool = False):
    """
    Scans runs_dir for run folders and loads metrics.
    Returns DataFrame with columns:
    [run_id, baseline, split, mode, backend, answer_rate, ...]
    """
    data = []

    if not runs_dir.exists():
        if strict:
            print(f"ERROR: Runs directory {runs_dir} not found.")
            sys.exit(1)
        return pd.DataFrame()

    for run_path in runs_dir.iterdir():
        if not run_path.is_dir():
            continue

        summary_path = run_path / "summary.json"
        config_path = run_path / "run_config.json"

        if not summary_path.exists():
            continue

        try:
            with open(summary_path) as f:
                s = json.load(f)

            cfg = {}
            if config_path.exists():
                with open(config_path) as f:
                    cfg = json.load(f)

            baseline = s.get("baseline", cfg.get("baseline", "unknown"))
            split = cfg.get("split", "unknown")
            mode = cfg.get("mode", cfg.get("args", {}).get("mode", "unknown"))
            backend_requested = cfg.get("backend_requested", cfg.get("backend", "unknown"))
            backend_used = cfg.get("backend_used", cfg.get("backend", "unknown"))
            run_name = run_path.name

            ablations = cfg.get("ablations", {})
            is_no_rerank = ablations.get("no_rerank", False)
            is_no_verify = ablations.get("no_verify", False)

            variant = baseline
            if baseline == "b3":
                if is_no_rerank:
                    variant += " (no-rerank)"
                if is_no_verify:
                    variant += " (no-verify)"

            def get_metric(key):
                val = s.get(key)
                if val is None or val == "N/A":
                    return np.nan
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return np.nan

            row = {
                "run_id": run_name,
                "baseline": baseline,
                "variant": variant,
                "split": split,
                "mode": mode,
                "backend_requested": backend_requested,
                "backend_used": backend_used,
                "backend": backend_used,  # backward-compatible alias used in existing plots
                "answer_rate": get_metric("answer_rate"),
                "abstention_accuracy": get_metric("abstention_accuracy"),
                "evidence_recall": get_metric("evidence_recall_at_5"),
                "evidence_mrr": get_metric("evidence_mrr"),
                "citation_precision": get_metric("citation_precision"),
                "citation_recall": get_metric("citation_recall"),
                "ungrounded_rate": get_metric("ungrounded_rate"),
                "contradiction_recall": get_metric("contradiction_recall"),
                "support_rate_mean": get_metric("support_rate_mean"),
            }
            data.append(row)

        except Exception as e:
            print(f"Warning: Failed to load {run_path}: {e}")

    return pd.DataFrame(data)


def check_requirements(df: pd.DataFrame, figure_name: str, strict: bool, out_fig_dir: Path):
    """In strict mode, fail with explicit list of missing runs."""
    if not strict:
        return

    reqs = REQUIRED_RUNS.get(figure_name, [])
    missing = []
    for r in reqs:
        matches = df[
            (df["baseline"] == r["baseline"]) &
            (df["split"] == r["split"])
        ]
        if matches.empty:
            missing.append(f"{r['baseline']}/{r['split']}")

    if missing:
        print(f"STRICT ERROR: {figure_name} requires runs that are missing: {missing}")
        print("Available runs:")
        if not df.empty:
            print(df[["run_id", "baseline", "split", "variant", "mode", "backend"]].to_string())
        else:
            print("  (none)")
        sys.exit(1)


def save_fig(fig, name: str, out_fig_dir: Path):
    out_fig_dir.mkdir(parents=True, exist_ok=True)
    path = out_fig_dir / f"{name}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"Saved {path}")
    plt.close(fig)


def make_fig_baselines(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    check_requirements(df, "fig_baselines", strict, out_fig_dir)

    mask = (df["split"] == "test") & (df["variant"].isin(["b1", "b2", "b3"]))
    plot_df = df[mask].copy()

    if plot_df.empty:
        if strict:
            print("STRICT ERROR: fig_baselines has no data after filter.")
            sys.exit(1)
        print("Skipping fig_baselines (no data)")
        return

    metrics = ["answer_rate", "abstention_accuracy", "ungrounded_rate"]
    fig, ax = plt.subplots(figsize=(8, 5))
    variants = [v for v in ["b1", "b2", "b3"] if v in set(plot_df["variant"].tolist())]
    _plot_grouped_metrics(ax, plot_df, metrics, variants)
    ax.set_title("Baseline Comparison (Test Set)")
    ax.set_ylim(0, 1.05)
    ax.legend()
    save_fig(fig, "fig_baselines", out_fig_dir)


def make_fig_retrieval(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    check_requirements(df, "fig_retrieval", strict, out_fig_dir)

    mask = (df["split"] == "test") & (df["variant"].isin(["b2", "b3"]))
    plot_df = df[mask].copy()

    if plot_df.empty:
        if strict:
            print("STRICT ERROR: fig_retrieval has no data after filter.")
            sys.exit(1)
        print("Skipping fig_retrieval (no data)")
        return

    metrics = ["evidence_recall", "evidence_mrr", "citation_precision"]
    fig, ax = plt.subplots(figsize=(8, 5))
    variants = [v for v in ["b2", "b3"] if v in set(plot_df["variant"].tolist())]
    _plot_grouped_metrics(ax, plot_df, metrics, variants)
    ax.set_title("Retrieval & Citation Quality (Test Set)")
    ax.set_ylim(0, 1.05)
    ax.legend()
    save_fig(fig, "fig_retrieval", out_fig_dir)


def make_fig_groundedness(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    """B3 groundedness: ungrounded_rate, support_rate. N/A if verification not performed."""
    check_requirements(df, "fig_groundedness", strict, out_fig_dir)

    mask = (df["split"] == "test") & (df["baseline"] == "b3")
    plot_df = df[mask].copy()

    if plot_df.empty:
        if strict:
            print("STRICT ERROR: fig_groundedness has no B3 test data.")
            sys.exit(1)
        print("Skipping fig_groundedness (no B3 data)")
        return

    metrics = ["ungrounded_rate", "citation_precision", "citation_recall"]
    if "support_rate_mean" in plot_df.columns and plot_df["support_rate_mean"].notna().any():
        metrics.append("support_rate_mean")

    fig, ax = plt.subplots(figsize=(8, 5))
    variants = list(dict.fromkeys(plot_df["variant"].tolist()))
    _plot_grouped_metrics(ax, plot_df, metrics, variants)
    ax.set_title("Groundedness (B3 Test Set)")
    ax.set_ylim(0, 1.05)
    ax.legend()
    save_fig(fig, "fig_groundedness", out_fig_dir)


def make_fig_tradeoff(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    """Coverage vs groundedness tradeoff (e.g. answer_rate vs 1 - ungrounded_rate)."""
    check_requirements(df, "fig_tradeoff", strict, out_fig_dir)

    mask = (df["split"] == "test")
    plot_df = df[mask].copy()

    if plot_df.empty:
        if strict:
            print("STRICT ERROR: fig_tradeoff has no test data.")
            sys.exit(1)
        print("Skipping fig_tradeoff (no data)")
        return

    # Use answer_rate as coverage; use (1 - ungrounded_rate) as groundedness where available, else citation_precision
    plot_df = plot_df.copy()
    plot_df["coverage"] = plot_df["answer_rate"]
    ur = plot_df["ungrounded_rate"]
    plot_df["groundedness"] = np.where(
        pd.notna(ur) & np.isfinite(ur),
        1.0 - ur,
        plot_df["citation_precision"]
    )

    fig, ax = plt.subplots(figsize=(6, 5))
    for variant in plot_df["variant"].unique():
        sub = plot_df[plot_df["variant"] == variant]
        ax.scatter(sub["coverage"], sub["groundedness"], label=variant, s=80, alpha=0.8)
    ax.set_xlabel("Coverage (answer rate)")
    ax.set_ylabel("Groundedness (1 - ungrounded_rate or citation precision)")
    ax.set_title("Coverage vs Groundedness (Test Set)")
    ax.legend()
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    save_fig(fig, "fig_tradeoff", out_fig_dir)


def save_tables(df: pd.DataFrame, out_table_dir: Path):
    """Export run summary table to results/tables."""
    out_table_dir.mkdir(parents=True, exist_ok=True)
    path = out_table_dir / "run_summary.csv"
    df.to_csv(path, index=False)
    print(f"Saved {path}")


def write_manifest(df: pd.DataFrame, runs_dir: Path, out_fig_dir: Path, out_table_dir: Path):
    """Write make_figures artifact manifest consumed by verify_artifacts."""
    root = Path(__file__).resolve().parent.parent.parent
    manifest_path = root / "results" / "manifest.json"
    runs = sorted(set(df["run_id"].tolist())) if "run_id" in df.columns else []
    figures = sorted([p.name for p in out_fig_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"]) if out_fig_dir.exists() else []
    tables = sorted([p.name for p in out_table_dir.iterdir() if p.is_file() and p.suffix.lower() == ".csv"]) if out_table_dir.exists() else []
    manifest = {
        "source": "make_figures.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs_dir": str(runs_dir),
        "runs": runs,
        "figures": figures,
        "tables": tables,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate figures and tables from results/runs.")
    parser.add_argument("--runs_dir", default="results/runs", help="Directory of run folders")
    parser.add_argument("--out_fig_dir", default="results/figures", help="Output directory for PNG figures")
    parser.add_argument("--out_table_dir", default="results/tables", help="Output directory for CSV tables")
    parser.add_argument("--strict", action="store_true",
                        help="Fail with exit 1 if required runs (b1/b2/b3 test) are missing")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    out_fig_dir = Path(args.out_fig_dir)
    out_table_dir = Path(args.out_table_dir)

    df = load_run_data(runs_dir, args.strict)
    if df.empty:
        print("No run data found.")
        if args.strict:
            sys.exit(1)
        return

    print(f"Loaded {len(df)} runs.")
    print(df[["run_id", "baseline", "split", "variant", "mode", "backend"]].to_string())

    make_fig_baselines(df, args.strict, out_fig_dir)
    make_fig_retrieval(df, args.strict, out_fig_dir)
    make_fig_groundedness(df, args.strict, out_fig_dir)
    make_fig_tradeoff(df, args.strict, out_fig_dir)
    save_tables(df, out_table_dir)
    write_manifest(df, runs_dir, out_fig_dir, out_table_dir)

    print("Done.")


if __name__ == "__main__":
    main()
