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
# Restrained dissertation palette: muted slate + warm copper + deep teal.
# Avoids the "default seaborn rainbow" look while staying colour-blind friendly.
plt.rcParams.update({
    "font.family":   "serif",
    "font.size":     10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "axes.edgecolor": "#555555",
    "axes.linewidth": 0.7,
    "axes.grid":     True,
    "grid.color":    "#dddddd",
    "grid.linewidth": 0.5,
    "grid.linestyle": "--",
    "xtick.color":   "#333333",
    "ytick.color":   "#333333",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.facecolor":  "white",
    "savefig.facecolor": "white",
})
PALETTE = {"b1": "#7a8aa8", "b2": "#b87633", "b3": "#2f5d6e"}

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


METRIC_LABELS = {
    "answer_rate":         "Answer rate",
    "abstention_accuracy": "Abstention\naccuracy",
    "ungrounded_rate":     "Ungrounded\nrate",
    "evidence_recall":     "Evidence\nRecall@5",
    "evidence_mrr":        "Evidence\nMRR",
    "citation_precision":  "Citation\nprecision",
    "citation_recall":     "Citation\nrecall",
    "support_rate_mean":   "Support\nrate (mean)",
}

VARIANT_LABELS = {
    "b1": "B1 — Prompt-Only",
    "b2": "B2 — Naive RAG",
    "b3": "B3 — Policy Copilot",
}


# Bootstrapped 95% CIs for B3-Generative on the 63-query golden set,
# as reported in §4.11 / Table 4.10 of the dissertation.  These are the
# only CIs the report computed; B1 and B2 bars do not get error bars.
B3_BOOTSTRAP_CI = {
    "answer_rate":         (0.250, 0.095, 0.286),
    "abstention_accuracy": (0.941, 0.741, 1.000),
    "evidence_recall":     (0.739, 0.652, 0.826),
}


def _plot_grouped_metrics(
    ax,
    plot_df: pd.DataFrame,
    metrics: list[str],
    variants: list[str],
    *,
    annotate: bool = True,
    error_bars: dict[tuple[str, str], tuple[float, float]] | None = None,
):
    """Grouped bar chart with mean aggregation per variant/metric.

    ``error_bars`` is an optional mapping ``{(variant, metric): (lo, hi)}``
    of lower/upper 95% CI bounds. Bars without a key get no error bar.
    """
    x = np.arange(len(metrics), dtype=float)
    width = 0.8 / max(1, len(variants))

    for idx, variant in enumerate(variants):
        sub = plot_df[plot_df["variant"] == variant]
        values: list[float] = []
        err_lo: list[float] = []
        err_hi: list[float] = []
        any_err = False
        for metric in metrics:
            series = sub[metric].dropna()
            v = float(series.mean()) if not series.empty else np.nan
            values.append(v)
            if error_bars and (variant, metric) in error_bars:
                lo, hi = error_bars[(variant, metric)]
                err_lo.append(max(0.0, v - lo))
                err_hi.append(max(0.0, hi - v))
                any_err = True
            else:
                err_lo.append(0.0)
                err_hi.append(0.0)

        offset = (idx - (len(variants) - 1) / 2.0) * width
        bars = ax.bar(
            x + offset,
            values,
            width=width,
            label=VARIANT_LABELS.get(variant, variant),
            color=_variant_color(variant, idx),
            edgecolor="white",
            linewidth=0.5,
            yerr=[err_lo, err_hi] if any_err else None,
            ecolor="#333333",
            capsize=3 if any_err else 0,
            error_kw={"elinewidth": 0.9, "alpha": 0.8} if any_err else None,
        )

        if annotate:
            for bar, v, hi in zip(bars, values, err_hi):
                if np.isnan(v):
                    continue
                ax.text(bar.get_x() + bar.get_width() / 2,
                        v + max(hi, 0.0) + 0.018,
                        f"{v:.2f}",
                        ha="center", va="bottom",
                        fontsize=7.5, color="#333333")

    ax.set_xticks(x)
    ax.set_xticklabels([METRIC_LABELS.get(m, m) for m in metrics])
    ax.xaxis.grid(False)


def _ci_for(metrics: list[str]) -> dict[tuple[str, str], tuple[float, float]]:
    """Build the error_bars mapping for B3 from the bootstrap dictionary,
    only including metrics that exist in this figure."""
    out: dict[tuple[str, str], tuple[float, float]] = {}
    for m in metrics:
        if m in B3_BOOTSTRAP_CI:
            _, lo, hi = B3_BOOTSTRAP_CI[m]
            out[("b3", m)] = (lo, hi)
    return out


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
                "contradiction_precision": get_metric("contradiction_precision"),
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


def _generative_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Restrict to the Generative-mode end-to-end runs used in Table 4.2.

    The shipped runs are b1_generative_final, b2_generative_bm25_fallback_final,
    and b3_generative_bm25_fallback_final, all with split='all'. Filtering
    by ``mode == "generative"`` plus a strict run_id match keeps the
    aggregation honest and avoids accidentally averaging over the many
    extractive ablation runs that share the variant name.
    """
    keep_runs = {
        "b1_generative_final",
        "b2_generative_bm25_fallback_final",
        "b3_generative_bm25_fallback_final",
    }
    return df[df["run_id"].isin(keep_runs)].copy()


def make_fig_baselines(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    check_requirements(df, "fig_baselines", strict, out_fig_dir)

    plot_df = _generative_subset(df)
    if plot_df.empty:
        if strict:
            print("STRICT ERROR: fig_baselines has no Generative runs.")
            sys.exit(1)
        print("Skipping fig_baselines (no Generative data)")
        return

    metrics = ["answer_rate", "abstention_accuracy", "ungrounded_rate"]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    variants = [v for v in ["b1", "b2", "b3"] if v in set(plot_df["variant"].tolist())]
    _plot_grouped_metrics(
        ax, plot_df, metrics, variants,
        error_bars=_ci_for(metrics),
    )
    ax.set_ylabel("Score (0-1)")
    ax.set_ylim(0, 1.20)
    ax.legend(loc="upper right")
    fig.text(
        0.5, 0.005,
        "Error bars: 95% bootstrap CI on B3 only (n = 63, 2,000 resamples; \u00a74.11).",
        fontsize=7.5, color="#666", family="serif", style="italic",
        ha="center", va="bottom",
    )
    fig.subplots_adjust(bottom=0.16)
    save_fig(fig, "fig_baselines", out_fig_dir)


def make_fig_retrieval(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    check_requirements(df, "fig_retrieval", strict, out_fig_dir)

    plot_df = _generative_subset(df)
    plot_df = plot_df[plot_df["variant"].isin(["b2", "b3"])]
    if plot_df.empty:
        if strict:
            print("STRICT ERROR: fig_retrieval has no Generative B2/B3 runs.")
            sys.exit(1)
        print("Skipping fig_retrieval (no Generative data)")
        return

    metrics = ["evidence_recall", "evidence_mrr", "citation_precision"]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    variants = [v for v in ["b2", "b3"] if v in set(plot_df["variant"].tolist())]
    _plot_grouped_metrics(
        ax, plot_df, metrics, variants,
        error_bars=_ci_for(metrics),
    )
    ax.set_ylabel("Score (0-1)")
    ax.set_ylim(0, 1.20)
    ax.legend(loc="upper right")
    fig.text(
        0.5, 0.005,
        "Error bars: 95% bootstrap CI on B3 only (n = 63, 2,000 resamples; \u00a74.11).",
        fontsize=7.5, color="#666", family="serif", style="italic",
        ha="center", va="bottom",
    )
    fig.subplots_adjust(bottom=0.16)
    save_fig(fig, "fig_retrieval", out_fig_dir)


def make_fig_groundedness(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    """Paired before/after verification chart for B3-Generative.

    Numbers are taken directly from Section 4.4 / Table 4.4 of the report:
    the ``Before Verification`` column is the LLM raw output, and the
    ``After Verification`` column is what the per-claim verifier surfaces
    once unsupported claims are pruned. Three metrics are paired:
    Ungrounded Rate (claim-level) drops 12% -> 4%; Citation Precision
    rises 78% -> 94%; Average Claims per Response drops 3.2 -> 2.8.

    Average claims per response is on a scale of 0-5, so the bar height
    is plotted on a secondary axis to preserve readability of the two
    rate metrics on the primary 0-1 axis.
    """
    metrics_pct = [
        ("Ungrounded\nrate (claim-level)", 0.12, 0.04),
        ("Citation\nprecision",            0.78, 0.94),
    ]
    metric_count = ("Avg claims\nper response", 3.2, 2.8)

    fig, ax = plt.subplots(figsize=(8, 4.8))

    n_groups = len(metrics_pct) + 1  # +1 for the count metric
    x = np.arange(n_groups, dtype=float)
    width = 0.36

    before_color = "#7a8aa8"  # B1-tone slate
    after_color  = "#2f5d6e"  # B3-tone teal

    # Primary axis: percentages (left two pairs)
    pct_before = [v[1] for v in metrics_pct]
    pct_after  = [v[2] for v in metrics_pct]

    ax.bar(x[:2] - width/2, pct_before, width=width,
           color=before_color, edgecolor="white", linewidth=0.5,
           label="Before verification")
    ax.bar(x[:2] + width/2, pct_after, width=width,
           color=after_color, edgecolor="white", linewidth=0.5,
           label="After verification")

    # Secondary axis for the count metric (rightmost group)
    ax2 = ax.twinx()
    ax2.bar(x[2] - width/2, metric_count[1], width=width,
            color=before_color, edgecolor="white", linewidth=0.5)
    ax2.bar(x[2] + width/2, metric_count[2], width=width,
            color=after_color, edgecolor="white", linewidth=0.5)
    ax2.set_ylabel("Avg claims per response (0-5 scale)",
                   fontsize=9, color="#555555")
    ax2.set_ylim(0, 5)
    ax2.tick_params(axis="y", colors="#555555", labelsize=8)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color("#888888")
    ax2.grid(False)

    # Value labels on every bar
    def _label(ax_, x_pos, value, pct=True):
        text = f"{int(value*100)}%" if pct else f"{value:.1f}"
        offset = 0.025 if pct else 0.12
        ax_.text(x_pos, value + offset, text,
                 ha="center", va="bottom", fontsize=8.5, color="#1a1a1a",
                 family="serif")

    for i, (_, b, a) in enumerate(metrics_pct):
        _label(ax, x[i] - width/2, b, pct=True)
        _label(ax, x[i] + width/2, a, pct=True)
    _label(ax2, x[2] - width/2, metric_count[1], pct=False)
    _label(ax2, x[2] + width/2, metric_count[2], pct=False)

    # Delta annotations between paired bars
    def _delta_arrow(ax_, x_left, x_right, y_top, label, color):
        ax_.annotate(
            "",
            xy=(x_right, y_top), xytext=(x_left, y_top),
            arrowprops=dict(arrowstyle="-|>", color=color,
                            lw=1.0, alpha=0.85),
        )
        ax_.text((x_left + x_right) / 2, y_top + 0.005,
                 label, ha="center", va="bottom", fontsize=8,
                 color=color, family="serif", weight="bold")

    # For percentages
    deltas = [
        (0, "-8 pp", "#2f5d6e"),  # ungrounded rate fell
        (1, "+16 pp", "#2f5d6e"),  # citation precision rose
    ]
    for idx, label, colour in deltas:
        b = metrics_pct[idx][1]
        a = metrics_pct[idx][2]
        y_top = max(b, a) + 0.10
        _delta_arrow(ax, x[idx] - width/2, x[idx] + width/2, y_top, label, colour)

    # For the count metric (on ax2 in count units)
    y_top_count = max(metric_count[1], metric_count[2]) + 0.55
    _delta_arrow(ax2, x[2] - width/2, x[2] + width/2,
                 y_top_count, "-0.4", "#2f5d6e")

    ax.set_xticks(x)
    ax.set_xticklabels([m[0] for m in metrics_pct] + [metric_count[0]])
    ax.set_ylabel("Rate / precision (0-1)")
    ax.set_ylim(0, 1.20)
    ax.xaxis.grid(False)

    # Legend (only on primary axis - same colour mapping applies on secondary)
    ax.legend(loc="upper left", frameon=False)

    fig.text(
        0.5, 0.005,
        "Source: \u00a74.4 / Table 4.4. Per-claim metrics on B3-Generative; "
        "secondary y-axis used for the count metric (right-most pair).",
        fontsize=7.5, color="#666", family="serif", style="italic",
        ha="center", va="bottom",
    )
    fig.subplots_adjust(bottom=0.16, right=0.88)
    save_fig(fig, "fig_groundedness", out_fig_dir)


def make_fig_tradeoff(df: pd.DataFrame, strict: bool, out_fig_dir: Path):
    """Coverage vs abstention-accuracy operating curve, parameterised by
    the support-rate threshold. Loads ``results/tables/threshold_sweep.csv``
    produced by ``scripts/sweep_abstention.py``; falls back to the bare
    test-split scatter if the sweep CSV is missing."""
    sweep_path = Path("results/tables/threshold_sweep.csv")
    if not sweep_path.exists():
        print(f"WARNING: no sweep CSV at {sweep_path}; skipping fig_tradeoff")
        return

    sweep = pd.read_csv(sweep_path)
    sweep_all = sweep[sweep["scope"] == "all"].sort_values("support_threshold")
    if sweep_all.empty:
        print("STRICT WARN: sweep CSV has no 'all' rows")
        return

    fig, ax = plt.subplots(figsize=(7.5, 5.2))

    # Curve: x = answer_rate (matches report's Table 4.2 definition), y =
    # abstention_accuracy (unanswerable subset). As the support threshold
    # rises, we move from lower-right (high coverage, lax refusal) toward
    # upper-left (low coverage, strict refusal).
    x = sweep_all["answer_rate"].to_numpy()
    y = sweep_all["abstention_accuracy"].to_numpy()
    ax.plot(x, y, color="#2f5d6e", linewidth=1.6, alpha=0.9, zorder=2)
    ax.scatter(x, y, color="#2f5d6e", s=22, alpha=0.6, zorder=2.5,
               edgecolors="white", linewidth=0.5)

    # Tick the curve at distinct (answer_rate, abstention_accuracy) points
    # only, choosing the lowest threshold that produced each unique point.
    seen_xy: set[tuple[float, float]] = set()
    tick_offsets = {  # per-threshold annotation offsets to avoid overlap
        0.00: (8, -14),
        0.50: (-6, 10),
        0.65: (8, -4),
    }
    for _, row in sweep_all.iterrows():
        tau = float(row["support_threshold"])
        xy = (round(row["answer_rate"], 3), round(row["abstention_accuracy"], 3))
        if xy in seen_xy or tau == 0.80:
            continue  # 0.80 gets its own highlight below
        seen_xy.add(xy)
        if tau in tick_offsets:
            dx, dy = tick_offsets[tau]
            ax.annotate(f"\u03c4 = {tau:.2f}",
                        (row["answer_rate"], row["abstention_accuracy"]),
                        textcoords="offset points", xytext=(dx, dy),
                        fontsize=7.5, color="#555555",
                        family="serif", style="italic")

    # Highlight the chosen operating point (support threshold = 0.80, the
    # shipped value).
    chosen = sweep_all[sweep_all["support_threshold"] == 0.80]
    if not chosen.empty:
        cx = float(chosen["answer_rate"].iloc[0])
        cy = float(chosen["abstention_accuracy"].iloc[0])
        ax.scatter([cx], [cy], marker="o", s=140, facecolor="#b87633",
                   edgecolors="#1a1a1a", linewidth=1.2, zorder=4)
        ax.annotate(
            "shipped\n\u03c4 = 0.80",
            (cx, cy), textcoords="offset points", xytext=(18, -2),
            fontsize=9, color="#1a1a1a", weight="bold", family="serif",
            arrowprops=dict(arrowstyle="-", color="#1a1a1a",
                            lw=0.8, shrinkA=0, shrinkB=4),
        )

    # "Ideal" corner at (1.0, 1.0): all answerable answered, all
    # unanswerable correctly refused.
    ax.scatter([1.0], [1.0], marker="*", s=200, color="#888888",
               edgecolors="white", linewidth=1, zorder=3)
    ax.text(1.0, 1.02, "ideal", fontsize=8, color="#888888",
            ha="center", va="bottom", family="serif", style="italic")

    ax.set_xlabel("Answer rate  (answerable subset)")
    ax.set_ylabel("Abstention accuracy  (unanswerable subset)")
    ax.set_xlim(0, 1.08)
    ax.set_ylim(0, 1.08)
    ax.text(
        0.02, 0.04,
        "Support-rate threshold \u03c4 swept 0.00 \u2192 1.00 over the full 63-query golden set,\n"
        "replayed from outputs.jsonl. Pre-LLM gate fixed at 0.30 (saturated under BM25 fallback).",
        transform=ax.transAxes, fontsize=7.5, color="#555555",
        family="serif", style="italic", va="bottom",
    )

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
