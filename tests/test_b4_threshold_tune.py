"""Phase 2 tests: B4 overlap threshold tuning.

Verifies:
  1. The tuning script is deterministic (same input → same output).
  2. The selected threshold is strictly below 0.10 (an improvement) and
     above 0.04 (a sanity sanity floor).
  3. At the selected threshold, dev-split simulated AbsAcc is 1.0
     (the strict selection rule).
  4. The DEFAULTS in conservative_hybrid.py have been updated to match.
  5. The B4 v3 run summary reflects the new threshold (AR > 0.45,
     AbsAcc == 1.0).
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TUNE_CSV = ROOT / "results/tables/b4_threshold_tune_dev.csv"
TUNE_SCRIPT = ROOT / "scripts/tune_b4_overlap_threshold.py"
B4_RUN_SUMMARY = ROOT / "results/runs/b4_conservative_hybrid_replay_v2_final/summary.json"


def _rows():
    with TUNE_CSV.open() as f:
        return list(csv.DictReader(f))


def test_tune_csv_exists_and_has_rows():
    assert TUNE_CSV.exists()
    rows = _rows()
    assert len(rows) >= 5
    # Each row has the expected fields
    expected = {"candidate_threshold", "dev_answer_rate", "dev_abstention_accuracy", "selected"}
    assert expected.issubset(set(rows[0].keys()))


def test_selected_threshold_strictly_below_010_and_above_004():
    rows = _rows()
    selected = next((r for r in rows if r["selected"] == "True"), None)
    assert selected is not None, "no row marked selected"
    val = float(selected["candidate_threshold"])
    assert 0.04 < val < 0.10, f"selected threshold {val} outside (0.04, 0.10)"


def test_selected_threshold_keeps_dev_abstention_accuracy_at_1():
    rows = _rows()
    selected = next((r for r in rows if r["selected"] == "True"), None)
    assert selected is not None
    assert float(selected["dev_abstention_accuracy"]) == 1.0


def test_defaults_in_conservative_hybrid_match_selected():
    from policy_copilot.service.conservative_hybrid import DEFAULTS
    rows = _rows()
    selected = next((r for r in rows if r["selected"] == "True"), None)
    assert selected is not None
    expected = float(selected["candidate_threshold"])
    assert abs(DEFAULTS["b4_overlap_threshold"] - expected) < 1e-6, (
        f"DEFAULTS overlap threshold {DEFAULTS['b4_overlap_threshold']} "
        f"does not match Phase-2 selected {expected}"
    )


def test_b4_run_summary_reflects_threshold_change():
    s = json.loads(B4_RUN_SUMMARY.read_text())
    # AR must have improved from the v2 baseline of 0.45
    assert s["answer_rate"] > 0.45, f"B4 AR {s['answer_rate']} did not improve over v2 baseline"
    # AbsAcc must still be at 1.0 (we never traded safety for coverage)
    assert s["abstention_accuracy"] == 1.0
    # Ungrounded floor held
    assert s["ungrounded_rate"] == 0.0
    # Citation Precision held
    assert s["citation_precision"] >= 0.95


def test_tune_script_deterministic(tmp_path):
    out1 = tmp_path / "a.csv"
    out2 = tmp_path / "b.csv"
    for out in (out1, out2):
        proc = subprocess.run(
            [sys.executable, str(TUNE_SCRIPT), "--out-csv", str(out)],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
    # The CSV content should be identical across runs
    assert out1.read_text() == out2.read_text(), "tuning script not deterministic"
