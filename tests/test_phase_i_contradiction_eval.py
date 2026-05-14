"""Phase I tests: contradiction re-evaluation after detector upgrade."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_CSV = ROOT / "results/tables/contradiction_evaluation_v2.csv"


def test_contradiction_eval_csv_exists():
    assert EVAL_CSV.exists()
    with EVAL_CSV.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 2
    assert any("POST-upgrade" in (r.get("label") or "") for r in rows)


def test_upgraded_detector_does_not_regress_recall_vs_pre_upgrade():
    """The new detector should match or improve recall on the hybrid run."""
    with EVAL_CSV.open() as f:
        rows = {r["run_name"]: r for r in csv.DictReader(f)}
    pre = rows["b3_extractive_hybrid_v2_final"]
    post = rows["b3_extractive_hybrid_v2_contra_upgraded"]
    assert float(post["contradiction_recall"]) >= float(pre["contradiction_recall"]) - 1e-6


def test_upgraded_detector_precision_within_acceptable_band():
    """Precision shouldn't collapse — i.e., not drop more than 10pp below the pre-upgrade value."""
    with EVAL_CSV.open() as f:
        rows = {r["run_name"]: r for r in csv.DictReader(f)}
    pre = float(rows["b3_extractive_hybrid_v2_final"]["contradiction_precision"])
    post = float(rows["b3_extractive_hybrid_v2_contra_upgraded"]["contradiction_precision"])
    assert post >= pre - 0.10, f"precision collapsed: {pre} -> {post}"


def test_upgraded_run_summary_contains_contradiction_metrics():
    s = json.loads(
        (ROOT / "results/runs/b3_extractive_hybrid_v2_contra_upgraded/summary.json").read_text()
    )
    assert "contradiction_recall" in s
    assert "contradiction_precision" in s
