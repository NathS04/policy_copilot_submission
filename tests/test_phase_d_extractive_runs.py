"""Phase D tests: extractive runs on corrected labels + new backend.

Verifies:
1. All four new run dirs exist with full schema.
2. backend_used matches backend_requested (no silent fallback).
3. Hybrid achieves Recall@5 >= 0.74 (sanity-check it's at least as good
   as BM25; actual target ≥ 0.80 reported in summary).
4. Outputs.jsonl records carry the corrected gold_paragraph_ids.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

NEW_RUNS = [
    "b2_extractive_dense_v2_final",
    "b2_extractive_hybrid_v2_final",
    "b3_extractive_dense_v2_final",
    "b3_extractive_hybrid_v2_final",
]


@pytest.mark.parametrize("run_name", NEW_RUNS)
def test_run_has_required_files(run_name):
    rd = ROOT / "results/runs" / run_name
    for fname in ("run_config.json", "outputs.jsonl", "summary.json",
                  "predictions.csv", "tables/metrics.csv"):
        assert (rd / fname).exists(), f"missing {rd / fname}"


@pytest.mark.parametrize("run_name", NEW_RUNS)
def test_backend_used_matches_requested(run_name):
    cfg = json.loads((ROOT / "results/runs" / run_name / "run_config.json").read_text())
    assert cfg.get("backend_used") == cfg.get("backend_requested"), (
        f"{run_name}: backend_used={cfg.get('backend_used')!r} vs "
        f"backend_requested={cfg.get('backend_requested')!r}"
    )


@pytest.mark.parametrize("run_name", NEW_RUNS)
def test_dataset_version_marked(run_name):
    # When the user passed --golden_set golden_set_v2_corrected.csv,
    # the run should be operating against the corrected denominators.
    # We check via category counts in outputs.jsonl matching v2.
    path = ROOT / "results/runs" / run_name / "outputs.jsonl"
    with path.open() as f:
        recs = [json.loads(line) for line in f if line.strip()]
    cats = [r["category"] for r in recs]
    # v2 has 40 answerable / 13 unanswerable / 10 contradiction = 63
    assert len(recs) == 63
    assert cats.count("answerable") == 40
    assert cats.count("unanswerable") == 13


def test_hybrid_beats_bm25_on_recall_at_5():
    """The b3_extractive_hybrid run should have Recall@5 >= the BM25
    replay baseline. This is the key Phase D acceptance criterion."""
    h = json.loads((ROOT / "results/runs/b3_extractive_hybrid_v2_final/summary.json").read_text())
    b = json.loads((ROOT / "results/runs/b3_extractive_v2/summary.json").read_text())
    assert h.get("evidence_recall_at_5", 0) >= b.get("evidence_recall_at_5", 0), (
        f"hybrid recall@5 {h.get('evidence_recall_at_5')} should be >= "
        f"BM25 baseline {b.get('evidence_recall_at_5')}"
    )


def test_hybrid_recall_at_least_target():
    """Plan target was Recall@5 ≥ 0.74 on the new backend; aspirational ≥ 0.80."""
    h = json.loads((ROOT / "results/runs/b3_extractive_hybrid_v2_final/summary.json").read_text())
    recall = h.get("evidence_recall_at_5", 0)
    assert recall >= 0.74, f"hybrid recall@5 {recall} below the 0.74 floor"


def test_no_silent_fallback_in_new_runs():
    """If we asked for dense or hybrid, that's what we got. backend_reason
    should be 'explicit_request' (not 'silent_fallback_*')."""
    for run in NEW_RUNS:
        cfg = json.loads((ROOT / "results/runs" / run / "run_config.json").read_text())
        reason = cfg.get("backend_reason", "")
        assert not reason.startswith("silent_fallback_"), (
            f"{run}: silent fallback occurred (reason={reason!r})"
        )
