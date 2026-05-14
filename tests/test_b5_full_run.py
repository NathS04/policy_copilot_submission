"""Phase 8 tests: B5 final-round run integrity.

Verifies the final B5 run directory holds the headline metrics, all
metadata fields, and respects the cited-or-silent contract.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results/runs/b5_evidence_gated_hybrid_v3_final"


def _records():
    with (RUN_DIR / "outputs.jsonl").open() as f:
        return [json.loads(line) for line in f if line.strip()]


def test_run_has_required_files():
    for fname in ("run_config.json", "outputs.jsonl", "summary.json",
                  "predictions.csv", "tables/metrics.csv", "README.md"):
        assert (RUN_DIR / fname).exists(), f"missing {RUN_DIR / fname}"


def test_summary_meets_all_floors():
    s = json.loads((RUN_DIR / "summary.json").read_text())
    assert s["answer_rate"] >= 0.80, f"AR {s['answer_rate']} below 0.80 floor"
    assert s["abstention_accuracy"] >= 0.80, f"AbsAcc {s['abstention_accuracy']} below 0.80 floor"
    assert s["citation_precision"] >= 0.95, f"CitPrec {s['citation_precision']} below 0.95 floor"
    assert s["ungrounded_rate"] <= 0.05, f"Ungrounded {s['ungrounded_rate']} above 0.05 ceiling"


def test_run_config_provenance():
    cfg = json.loads((RUN_DIR / "run_config.json").read_text())
    assert cfg.get("baseline") == "b5"
    assert cfg.get("mode") == "evidence_gated_hybrid"
    assert cfg.get("backend_used") == "hybrid"
    bp = cfg.get("b5_provenance") or {}
    assert bp.get("no_llm_calls") is True
    assert bp.get("source_run") == "b3_extractive_hybrid_v2_final"
    assert "mode_counts" in bp


def test_every_surfaced_record_has_citation():
    """The cited-or-silent contract: any non-abstained B5 response must
    carry at least one citation referencing a real paragraph ID."""
    for r in _records():
        if r.get("is_abstained"):
            continue
        cits = r.get("citations") or []
        assert cits, f"{r.get('query_id')}: surfaced response missing citation"


def test_every_record_has_b5_metadata():
    required = {"mode_used", "answerability_decision", "answerability_reason",
                "evidence_strength", "gate_features"}
    for r in _records():
        missing = required - set(r.keys())
        assert not missing, f"{r.get('query_id')}: missing B5 fields {missing}"


def test_mode_counts_sum_to_total():
    cfg = json.loads((RUN_DIR / "run_config.json").read_text())
    counts = cfg["b5_provenance"]["mode_counts"]
    s = json.loads((RUN_DIR / "summary.json").read_text())
    assert sum(counts.values()) == s["total_queries"]


def test_failure_analysis_csv_exists_and_aligns():
    p = ROOT / "results/tables/b5_failure_analysis.csv"
    assert p.exists()
    with p.open() as f:
        rows = list(csv.DictReader(f))
    n_fps = sum(1 for r in rows if r["kind"] == "false_positive")
    n_fns = sum(1 for r in rows if r["kind"] == "false_negative")
    # Sanity: AbsAcc 0.8462 on 13 unanswerable = 11 correct = 2 FPs.
    assert n_fps == 2, f"expected 2 FPs, found {n_fps}"
    # AR 0.90 on 40 answerable = 36 correct = 4 FNs.
    assert n_fns == 4, f"expected 4 FNs, found {n_fns}"


def test_sweep_csv_exists_and_marks_selected():
    p = ROOT / "results/tables/b5_threshold_sweep_dev.csv"
    assert p.exists()
    with p.open() as f:
        rows = list(csv.DictReader(f))
    selected = [r for r in rows if r["selected"] == "True"]
    assert len(selected) == 1, f"expected 1 selected config, found {len(selected)}"
    s = selected[0]
    # selected config must project full-set AR >= 0.80
    assert float(s["full_answer_rate_proj"]) >= 0.80
    assert float(s["full_abstention_accuracy_proj"]) >= 0.80
