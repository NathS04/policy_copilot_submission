"""Phase J tests: bootstrap CIs over corrected denominators.

Verifies:
  1. The aggregated CSV exists and is non-empty.
  2. Each (run, metric) row has a sensible denominator (matches v2 set).
  3. B3-Generative v2 denominators match 40/13/50 etc.
  4. Determinism: rerunning the script produces identical CIs (seed=42).
  5. Confidence-interval order: lo <= point <= hi.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results/tables/statistical_confidence_v2.csv"
SCRIPT = ROOT / "scripts/compute_bootstrap_ci_v2.py"


def _rows():
    with OUT_CSV.open() as f:
        return list(csv.DictReader(f))


def test_csv_exists_and_has_rows():
    assert OUT_CSV.exists()
    rows = _rows()
    assert len(rows) >= 4  # at least one run with multiple metrics


def test_b3_generative_v2_denominators():
    rows = [r for r in _rows() if r["run_name"] == "b3_generative_v2"]
    assert rows
    by_metric = {r["metric"]: int(r["denominator_n"]) for r in rows}
    assert by_metric.get("answer_rate") == 40  # corrected answerable
    assert by_metric.get("abstention_accuracy") == 13  # corrected unanswerable
    # evidence_recall denominator: queries with non-empty gold = 40 + 10 contradiction = 50
    assert by_metric.get("evidence_recall_at_5") == 50


def test_b3_generative_v2_answer_rate_in_expected_window():
    rows = [r for r in _rows() if r["run_name"] == "b3_generative_v2"
            and r["metric"] == "answer_rate"]
    assert rows
    r = rows[0]
    pt = float(r["point_estimate"])
    lo = float(r["ci95_lo"])
    hi = float(r["ci95_hi"])
    assert pt == 0.25  # 10/40
    assert lo <= pt <= hi


def test_b3_extractive_hybrid_v2_recall_in_expected_window():
    rows = [r for r in _rows() if r["run_name"] == "b3_extractive_hybrid_v2_final"
            and r["metric"] == "evidence_recall_at_5"]
    assert rows
    r = rows[0]
    pt = float(r["point_estimate"])
    assert pt >= 0.74  # plan target floor


def test_ci_order_lo_le_point_le_hi():
    bad = []
    for r in _rows():
        lo = float(r["ci95_lo"])
        pt = float(r["point_estimate"])
        hi = float(r["ci95_hi"])
        if not (lo <= pt + 1e-9 and pt <= hi + 1e-9):
            bad.append((r["run_name"], r["metric"], lo, pt, hi))
    assert not bad, bad


def test_script_deterministic(tmp_path):
    """Running twice with the same seed produces identical CIs."""
    out1 = tmp_path / "a.csv"
    out2 = tmp_path / "b.csv"
    for out in (out1, out2):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--out-csv", str(out)],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
    assert out1.read_text() == out2.read_text(), "bootstrap not deterministic"
