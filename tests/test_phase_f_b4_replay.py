"""Phase F tests: B4 replay run exists with valid metrics.

Verifies:
  1. Replay run directory has all required files.
  2. B4 records carry mode_used + fallback_reason + evidence_strength.
  3. Mode counts sum to total queries.
  4. Extractive fallback rows have claim_verification.support_rate == 1.0
     (replaced from the LLM verification by the replay script).
  5. Safety floors: Abstention ≥ 80%, Ungrounded ≤ 5%, Citation Precision ≥ 95%.
  6. Answer Rate > B3-Generative baseline (uplift over the BM25-fallback
     B3 result).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results/runs/b4_conservative_hybrid_replay_v2_final"


def test_b4_run_has_required_files():
    for fname in ("run_config.json", "outputs.jsonl", "summary.json",
                  "predictions.csv", "tables/metrics.csv", "README.md"):
        assert (RUN_DIR / fname).exists(), f"missing {RUN_DIR / fname}"


def _records():
    with (RUN_DIR / "outputs.jsonl").open() as f:
        return [json.loads(l) for l in f if l.strip()]


def test_b4_records_have_mode_metadata():
    recs = _records()
    assert recs
    for r in recs:
        assert "mode_used" in r, f"missing mode_used in {r.get('query_id')}"
        assert r["mode_used"] in ("generative", "extractive_fallback", "abstained")
        assert "fallback_reason" in r
        assert "evidence_strength" in r


def test_b4_mode_counts_sum_to_total():
    cfg = json.loads((RUN_DIR / "run_config.json").read_text())
    counts = cfg["b4_replay_provenance"]["mode_counts"]
    summary = json.loads((RUN_DIR / "summary.json").read_text())
    assert sum(counts.values()) == summary["total_queries"]


def test_extractive_fallback_rows_have_clean_verification():
    recs = _records()
    fallbacks = [r for r in recs if r.get("mode_used") == "extractive_fallback"]
    assert fallbacks, "expected at least one extractive_fallback row"
    for r in fallbacks:
        cv = r.get("claim_verification")
        assert isinstance(cv, dict)
        assert cv.get("support_rate") == 1.0
        assert cv.get("unsupported_claims") == 0


def test_b4_safety_floors_held():
    s = json.loads((RUN_DIR / "summary.json").read_text())
    assert s["abstention_accuracy"] >= 0.80, f"abstention_accuracy={s['abstention_accuracy']}"
    assert s["ungrounded_rate"] <= 0.05, f"ungrounded_rate={s['ungrounded_rate']}"
    assert s["citation_precision"] >= 0.95, f"citation_precision={s['citation_precision']}"


def test_b4_answer_rate_beats_b3_generative():
    b4 = json.loads((RUN_DIR / "summary.json").read_text())
    b3 = json.loads((ROOT / "results/runs/b3_generative_v2/summary.json").read_text())
    assert b4["answer_rate"] > b3["answer_rate"], (
        f"B4 answer_rate {b4['answer_rate']} did not improve over "
        f"B3-Generative {b3['answer_rate']}"
    )


def test_abstained_rows_keep_insufficient_evidence():
    recs = _records()
    abstained = [r for r in recs if r.get("mode_used") == "abstained"]
    for r in abstained:
        assert (r.get("answer") or "").strip() == "INSUFFICIENT_EVIDENCE"
        assert r.get("is_abstained") is True


def test_extractive_fallback_citations_match_top_evidence():
    recs = _records()
    fallbacks = [r for r in recs if r.get("mode_used") == "extractive_fallback"]
    for r in fallbacks:
        cits = r.get("citations") or []
        evidence = r.get("evidence") or []
        assert cits, f"extractive_fallback row {r.get('query_id')} missing citation"
        # The single citation must be the top retrieved paragraph.
        assert cits[0] == evidence[0]["paragraph_id"], (
            f"row {r.get('query_id')}: citation {cits[0]} != "
            f"top evidence {evidence[0]['paragraph_id']}"
        )
