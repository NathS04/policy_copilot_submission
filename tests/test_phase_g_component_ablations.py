"""Phase G tests: real component ablations replace design-time estimates.

Verifies:
  1. component_ablation_final.csv exists and lists 5 rows.
  2. Each row has a matching run directory with run_config.json that
     reflects the disabled component.
  3. No row labelled 'estimate' (we now have real runs).
  4. The reference 'Full B3' row matches the standalone
     b3_extractive_hybrid_v2_final summary.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ABLATION_CSV = ROOT / "results/tables/component_ablation_final.csv"

EXPECTED = {
    "ablation_full_hybrid_v2":         ("Full B3",          "none"),
    "ablation_no_rerank_hybrid_v2":    ("minus Reranker",   "rerank"),
    "ablation_no_verify_hybrid_v2":    ("minus Verification", "verify"),
    "ablation_no_abstain_hybrid_v2":   ("minus Abstention Gate", "abstention"),
    "ablation_no_contra_hybrid_v2":    ("minus Contradiction Detection", "contradiction"),
}


def _rows():
    with ABLATION_CSV.open() as f:
        return list(csv.DictReader(f))


def test_csv_exists_and_has_five_rows():
    assert ABLATION_CSV.exists(), f"missing {ABLATION_CSV}"
    rows = _rows()
    assert len(rows) == 5, f"expected 5 rows, got {len(rows)}"


def test_no_row_labelled_estimate():
    for r in _rows():
        assert "estimate" not in (r.get("source", "").lower()), r


def test_each_row_has_matching_run_dir():
    for r in _rows():
        run = ROOT / "results/runs" / r["run_name"]
        assert run.exists(), f"missing run dir for {r['run_name']}"
        assert (run / "summary.json").exists()
        assert (run / "run_config.json").exists()
        assert (run / "outputs.jsonl").exists()


def test_run_config_reflects_disabled_component():
    for r in _rows():
        cfg = json.loads((ROOT / "results/runs" / r["run_name"] / "run_config.json").read_text())
        comp = r["component_disabled"]
        if comp == "rerank":
            assert cfg.get("ablations", {}).get("no_rerank") is True
        elif comp == "verify":
            assert cfg.get("ablations", {}).get("no_verify") is True
        elif comp == "contradiction":
            assert cfg.get("ablations", {}).get("no_contradictions") is True
        elif comp == "abstention":
            assert cfg.get("min_support_rate") == 0.0
            assert cfg.get("abstain_threshold") == 0.0
        # 'none' -> nothing disabled


def test_full_b3_row_matches_summary_json():
    rows = _rows()
    full = next((r for r in rows if r["run_name"] == "ablation_full_hybrid_v2"), None)
    assert full
    summary = json.loads((ROOT / "results/runs/ablation_full_hybrid_v2/summary.json").read_text())
    assert float(full["answer_rate"]) == summary["answer_rate"]
    assert float(full["abstention_accuracy"]) == summary["abstention_accuracy"]
    assert float(full["evidence_recall_at_5"]) == summary["evidence_recall_at_5"]
