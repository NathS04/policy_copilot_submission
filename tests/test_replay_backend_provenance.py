"""Phase 3 tests: explicit replay-provenance metadata + verify_artifacts notice.

Verifies:
  1. Each v2 replay run carries `replay_from_bm25_source: true`.
  2. Each carries a `replay_provenance.backend_source_run` pointing to
     the original BM25-fallback source run.
  3. verify_artifacts emits the new EXPECTED NOTICE for these runs (not a
     bare WARNING).
  4. The non-replay run `b3_extractive_hybrid_v2_final` does NOT emit the
     replay notice (its backend_used IS hybrid, no mismatch).
  5. verify_artifacts still exits 0.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts/verify_artifacts.py"

REPLAY_RUNS = [
    ("b2_generative_v2",                       "b2_generative_bm25_fallback_final"),
    ("b3_generative_v2",                       "b3_generative_bm25_fallback_final"),
    ("b4_conservative_hybrid_replay_v2_final", "b3_generative_bm25_fallback_final"),
]


def _cfg(run_name: str) -> dict:
    p = ROOT / "results/runs" / run_name / "run_config.json"
    return json.loads(p.read_text())


def test_replay_runs_have_explicit_flag():
    for run, _ in REPLAY_RUNS:
        cfg = _cfg(run)
        assert cfg.get("replay_from_bm25_source") is True, (
            f"{run} missing replay_from_bm25_source=True"
        )


def test_replay_runs_have_backend_source_metadata():
    for run, expected_source in REPLAY_RUNS:
        cfg = _cfg(run)
        rp = cfg.get("replay_provenance") or {}
        assert rp.get("backend_source_run") == expected_source, (
            f"{run}: backend_source_run={rp.get('backend_source_run')!r} "
            f"expected {expected_source!r}"
        )
        assert rp.get("backend_source_used") == "bm25"
        assert rp.get("replay_note"), f"{run} missing replay_note"


def test_verify_artifacts_emits_replay_notice():
    proc = subprocess.run(
        [sys.executable, str(VERIFY)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    for run, _ in REPLAY_RUNS:
        assert f"EXPECTED NOTICE: Run {run}: backend_requested=dense but backend_used=bm25" in out, (
            f"verify_artifacts did not emit replay notice for {run}\n--- stdout ---\n{out}"
        )
        # The replay-specific message
        assert "replay over the retained BM25-source outputs" in out


def test_verify_artifacts_no_warning_for_replay():
    """No bare WARNING line for v2 replay runs (they should be EXPECTED NOTICE)."""
    proc = subprocess.run(
        [sys.executable, str(VERIFY)],
        cwd=ROOT, capture_output=True, text=True,
    )
    out = proc.stdout
    # No line starting with "WARNING:" referencing a v2 replay run.
    for run, _ in REPLAY_RUNS:
        bad = f"WARNING: Run {run}"
        assert bad not in out, f"unexpected WARNING for replay run {run}"


def test_extractive_hybrid_has_no_replay_notice():
    """The non-replay extractive-hybrid run uses hybrid; no mismatch should fire."""
    cfg = _cfg("b3_extractive_hybrid_v2_final")
    assert cfg.get("backend_requested") == cfg.get("backend_used") == "hybrid"
    # And no replay marker
    assert not cfg.get("replay_from_bm25_source", False)
