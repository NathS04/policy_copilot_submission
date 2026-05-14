"""Consolidate v2 run summaries (Phase L).

Walks the v2 run directories and writes:
  - results/tables/run_summary_v2.csv  (one row per run with all key metrics)
  - docs/report/figures/fig_baselines_v2.png  (side-by-side comparison)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results/tables/run_summary_v2.csv"
OUT_FIG = ROOT / "docs/report/figures/fig_baselines_v2.png"

# (run_name, label, baseline)
RUNS = [
    ("b1_generative_v2",                       "B1 (replay)",            "b1"),
    ("b2_generative_v2",                       "B2-Gen (replay)",        "b2"),
    ("b2_extractive_hybrid_v2_final",          "B2-Ext (hybrid)",        "b2"),
    ("b3_generative_v2",                       "B3-Gen (replay)",        "b3"),
    ("b3_extractive_hybrid_v2_final",          "B3-Ext (hybrid)",        "b3"),
    ("b3_extractive_hybrid_v2_contra_upgraded","B3-Ext + new contra",    "b3"),
    ("b4_conservative_hybrid_replay_v2_final", "B4 Conservative Hybrid", "b4"),
]


KEYS = [
    "baseline", "total_queries",
    "answer_rate", "abstention_accuracy",
    "evidence_recall_at_5", "evidence_precision_at_5", "evidence_mrr",
    "citation_precision", "citation_recall",
    "ungrounded_rate", "support_rate_mean",
    "contradiction_recall", "contradiction_precision",
]


def _row(run_name: str, label: str, baseline: str) -> dict:
    p = ROOT / "results/runs" / run_name / "summary.json"
    if not p.exists():
        return {"run_name": run_name, "label": label, "baseline": baseline, "missing": True}
    s = json.loads(p.read_text())
    row = {"run_name": run_name, "label": label, "baseline_input": baseline}
    for k in KEYS:
        row[k] = s.get(k, "")
    return row


def write_csv(rows: List[dict]) -> None:
    fields = ["run_name", "label", "baseline_input"] + KEYS
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def plot_v2_baselines(rows: List[dict]) -> None:
    """Grouped bar chart: AR / AbsAcc / Recall@5 / CitPrec for the
    key v2 configurations (skips B1 because it has no retrieval)."""
    # Order: B2-Gen, B2-Ext, B3-Gen, B3-Ext, B4
    keep = {
        "B2-Gen (replay)": "B2-Gen",
        "B2-Ext (hybrid)": "B2-Ext",
        "B3-Gen (replay)": "B3-Gen",
        "B3-Ext (hybrid)": "B3-Ext",
        "B4 Conservative Hybrid": "B4",
    }
    plot_rows = [r for r in rows if r.get("label") in keep]
    labels = [keep[r["label"]] for r in plot_rows]

    def _f(r, key):
        v = r.get(key, "")
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    metrics = [
        ("answer_rate", "Answer Rate"),
        ("abstention_accuracy", "Abstention Acc."),
        ("evidence_recall_at_5", "Evidence Recall@5"),
        ("citation_precision", "Citation Precision"),
    ]
    x = list(range(len(labels)))
    n_metrics = len(metrics)
    bar_w = 0.18

    fig, ax = plt.subplots(figsize=(9.5, 4.5))
    palette = ["#7a8aa8", "#b87633", "#2f5d6e", "#4e79a7"]
    for i, (key, name) in enumerate(metrics):
        vals = [_f(r, key) for r in plot_rows]
        offsets = [xi + (i - (n_metrics - 1) / 2) * bar_w for xi in x]
        ax.bar(offsets, vals, width=bar_w, label=name, color=palette[i],
               edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Rate")
    ax.set_title("Final v2 results on the corrected golden set (hybrid backend)")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9, ncols=2)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG, dpi=160)
    plt.close(fig)


def main() -> int:
    rows = [_row(r, label, b) for r, label, b in RUNS]
    write_csv(rows)
    plot_v2_baselines(rows)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_FIG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
