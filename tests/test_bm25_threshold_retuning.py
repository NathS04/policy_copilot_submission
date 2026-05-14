"""Tests for scripts/analyse_bm25_threshold_retuning.py.

These tests use a small synthetic outputs.jsonl + golden_set.csv to
verify the gate semantics, selection rule, and gate G1 reconstruction
check. No real run directories are read; no LLM calls.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "analyse_bm25_threshold_retuning.py"


def _record(qid, category, support_rate, unsupported, max_rerank=1.0):
    cv = None
    if support_rate is not None:
        cv = {
            "claims": [],
            "supported_claims": 0,
            "unsupported_claims": unsupported,
            "support_rate": support_rate,
        }
    return {
        "query_id": qid,
        "category": category,
        "is_answerable": category == "answerable",
        "confidence": {"max_rerank": max_rerank},
        "claim_verification": cv,
        "answer": "x",
        "citations": [],
        "evidence": [],
    }


def _build_synthetic_run(run_dir: Path, golden_path: Path, records, summary):
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "outputs.jsonl").open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    (run_dir / "summary.json").write_text(json.dumps(summary))
    with golden_path.open("w") as f:
        f.write("query_id,category,split\n")
        for r in records:
            f.write(f"{r['query_id']},{r['category']},test\n")


def _run(tmp_path, records, summary, scope="all", extra=None):
    run_dir = tmp_path / "run"
    golden = tmp_path / "golden.csv"
    out_csv = tmp_path / "out.csv"
    out_sum = tmp_path / "summary.json"
    out_fig = tmp_path / "fig.png"
    _build_synthetic_run(run_dir, golden, records, summary)
    cmd = [
        sys.executable, str(SCRIPT),
        "--run-dir", str(run_dir),
        "--golden-set", str(golden),
        "--out-csv", str(out_csv),
        "--out-summary", str(out_sum),
        "--out-fig", str(out_fig),
        "--step", "0.05",
        "--scope", scope,
    ]
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc, out_csv, out_sum, out_fig


def _matched_denoms_records():
    """Build a synthetic 63-record run matching the real denominators
    so G2 passes. Numbers chosen so the conservative tau=0.80 reproduces
    a known synthetic summary."""
    records = []
    # 36 answerable: 9 with support_rate=1.0 (surface at 0.80), 27 with
    # support_rate=0.5 (do not surface at 0.80).
    for i in range(9):
        records.append(_record(f"a{i:02d}", "answerable", 1.0, 0))
    for i in range(27):
        records.append(_record(f"a{i+9:02d}", "answerable", 0.5, 1))
    # 17 unanswerable: 16 abstained at tau=0.80 (support_rate=0.5),
    # 1 surfaced at tau=0.80 (support_rate=1.0) -> abstention_acc=16/17.
    for i in range(16):
        records.append(_record(f"u{i:02d}", "unanswerable", 0.5, 1))
    records.append(_record("u16", "unanswerable", 1.0, 0))
    # 10 contradiction: all support_rate=0.5 (abstained at 0.80).
    for i in range(10):
        records.append(_record(f"c{i:02d}", "contradiction", 0.5, 1))
    return records


def test_g1_reconstructs_conservative_point(tmp_path):
    records = _matched_denoms_records()
    # 9 answerable surfaced out of 36 -> answer_rate = 0.25.
    # 16 of 17 unanswerable abstained -> 0.9412.
    # All 9 surfaced answerable have support_rate=1.0 and 0 unsupported
    # claims; the 1 surfaced unanswerable also has support_rate=1.0 and
    # 0 unsupported -> ungrounded_rate_response = 0.0.
    summary = {
        "answer_rate": 0.25,
        "abstention_accuracy": 0.9412,
        "ungrounded_rate": 0.0,
    }
    proc, _, out_sum, _ = _run(tmp_path, records, summary)
    assert proc.returncode == 0, f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    data = json.loads(out_sum.read_text())
    assert data["reconstructed_conservative_matches_summary_json"] is True
    assert data["conservative_answer_rate"] == 0.25
    assert abs(data["conservative_abstention_accuracy"] - 0.9412) < 1e-3
    assert data["conservative_ungrounded_rate_response"] == 0.0


def test_g1_fails_when_summary_disagrees(tmp_path):
    records = _matched_denoms_records()
    bad_summary = {
        "answer_rate": 0.95,           # forced mismatch
        "abstention_accuracy": 0.9412,
        "ungrounded_rate": 0.0,
    }
    proc, _, out_sum, _ = _run(tmp_path, records, bad_summary)
    assert proc.returncode != 0
    assert "G1" in proc.stderr
    # Summary JSON must NOT have been written.
    assert not out_sum.exists()


def test_tau_one_surfaces_nothing_synthetic(tmp_path):
    """Manually exercise metrics_at at tau=1.0 via importing the module."""
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        import importlib
        mod = importlib.import_module("analyse_bm25_threshold_retuning")
        records = _matched_denoms_records()
        m = mod.metrics_at(records, 1.0)
        # Only support_rate=1.0 records pass (>= 1.0). Those are 9 answerable
        # + 1 unanswerable = 10 surfaced.
        assert m["n_surfaced_total"] == 10
        # Drop tau to 1.01 -> nothing surfaces.
        m2 = mod.metrics_at(records, 1.01)
        assert m2["n_surfaced_total"] == 0
        assert m2["n_answered"] == 0
    finally:
        sys.path.pop(0)


def test_selection_rule_picks_lowest_tau_with_safe_constraints(tmp_path):
    """Synthetic case: only one tau satisfies both constraints; selection
    must pick the highest answer_rate subject to constraints."""
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        import importlib
        mod = importlib.import_module("analyse_bm25_threshold_retuning")
        # Construct sweep rows by hand.
        rows = [
            {  # below abstention floor
                "tau": 0.10, "answer_rate": 0.90, "abstention_accuracy": 0.50,
                "ungrounded_rate_response": 0.10, "n_answered": 30,
            },
            {  # feasible, high answer rate
                "tau": 0.50, "answer_rate": 0.70, "abstention_accuracy": 0.85,
                "ungrounded_rate_response": 0.02, "n_answered": 25,
            },
            {  # feasible, lower answer rate
                "tau": 0.70, "answer_rate": 0.40, "abstention_accuracy": 0.90,
                "ungrounded_rate_response": 0.0, "n_answered": 14,
            },
            {  # shipped
                "tau": 0.80, "answer_rate": 0.25, "abstention_accuracy": 0.9412,
                "ungrounded_rate_response": 0.0, "n_answered": 9,
            },
        ]
        chosen, interp = mod.select_operating_point(rows)
        assert interp == "balanced_point_meets_constraints"
        assert chosen["tau"] == 0.50
    finally:
        sys.path.pop(0)


def test_selection_falls_back_to_diagnostic(tmp_path):
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        import importlib
        mod = importlib.import_module("analyse_bm25_threshold_retuning")
        rows = [
            {
                "tau": 0.10, "answer_rate": 0.90, "abstention_accuracy": 0.10,
                "ungrounded_rate_response": 0.20, "n_answered": 30,
            },
            {
                "tau": 0.50, "answer_rate": 0.50, "abstention_accuracy": 0.40,
                "ungrounded_rate_response": 0.03, "n_answered": 18,
            },
        ]
        chosen, interp = mod.select_operating_point(rows)
        assert interp == "diagnostic_point_only"
        assert chosen["tau"] == 0.50


    finally:
        sys.path.pop(0)


def test_g2_denominator_mismatch_aborts(tmp_path):
    # 3 answerable, 1 unanswerable -> (4, 3, 1, 0) != (63, 36, 17, 10)
    records = [
        _record("a0", "answerable", 1.0, 0),
        _record("a1", "answerable", 1.0, 0),
        _record("a2", "answerable", 1.0, 0),
        _record("u0", "unanswerable", 0.0, 1),
    ]
    summary = {"answer_rate": 1.0, "abstention_accuracy": 1.0, "ungrounded_rate": 0.0}
    proc, _, out_sum, _ = _run(tmp_path, records, summary)
    assert proc.returncode != 0
    assert "G2" in proc.stderr
    assert not out_sum.exists()
