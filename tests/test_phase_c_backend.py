"""Phase C tests: dense + hybrid wired in, no silent fallback when disabled.

Covers:
  1. backend='dense' loads dense in the [ml] env, exposes
     dense_index_path and dense_index_sha.
  2. backend='hybrid' constructs RRF-fused dense+BM25 with paragraph-id
     dedup.
  3. allow_fallback=False raises BackendUnavailableError when dense load
     fails.
  4. backend='bm25_fallback' is explicit and records backend_reason.
  5. New run_eval --backend hybrid/bm25_fallback CLI flags accepted.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _ml_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        import faiss  # noqa: F401
        return True
    except Exception:
        return False


def _index_built() -> bool:
    return (ROOT / "data/corpus/processed/index/faiss.index").exists()


# ---------------------------------------------------------------- #
# 1. dense backend loads cleanly when [ml] deps + index present
# ---------------------------------------------------------------- #

@pytest.mark.skipif(not _ml_available() or not _index_built(),
                    reason="[ml] deps or dense index not present")
def test_dense_loads_and_records_provenance():
    from policy_copilot.retrieve.retriever import Retriever
    r = Retriever(backend="dense", allow_fallback=False)
    assert r.backend_requested == "dense"
    assert r.backend_used == "dense"
    assert r.backend_reason == "explicit_request"
    assert r.loaded is True
    assert r.dense_index_path is not None
    assert r.dense_index_sha is not None
    assert len(r.dense_index_sha) == 64  # sha256 hex


# ---------------------------------------------------------------- #
# 2. hybrid backend produces dedup'd fused results
# ---------------------------------------------------------------- #

@pytest.mark.skipif(not _ml_available() or not _index_built(),
                    reason="[ml] deps or dense index not present")
def test_hybrid_dedupes_by_paragraph_id_and_records_provenance():
    from policy_copilot.retrieve.retriever import Retriever
    r = Retriever(backend="hybrid", allow_fallback=False)
    assert r.backend_used == "hybrid"
    assert r.loaded is True
    results = r.retrieve("notice period resignation", k=5)
    assert results, "hybrid must return at least one result for a relevant query"
    pids = [x["paragraph_id"] for x in results]
    assert len(pids) == len(set(pids)), f"hybrid result list has duplicates: {pids}"
    # RRF metadata
    for x in results:
        assert x["backend"] in ("hybrid_rrf", "dense", "sparse")
        # fused_score may be None when only one side ran, but most realistic
        # queries hit both sides on a small synthetic corpus.


# ---------------------------------------------------------------- #
# 3. allow_fallback=False raises when dense unavailable
# ---------------------------------------------------------------- #

def test_dense_strict_raises_when_load_fails():
    from policy_copilot.retrieve.retriever import Retriever, BackendUnavailableError
    # Force a load failure by pointing at a non-existent index dir.
    with pytest.raises(BackendUnavailableError):
        Retriever(backend="dense", index_dir="/nonexistent/path", allow_fallback=False)


def test_dense_allow_fallback_keeps_old_behaviour():
    """Default allow_fallback=True must preserve backward-compat: silent fallback."""
    from policy_copilot.retrieve.retriever import Retriever
    r = Retriever(backend="dense", index_dir="/nonexistent/path", allow_fallback=True)
    # Either dense load succeeded (env has index) or fell back to bm25 with a reason.
    assert r.backend_requested == "dense"
    if r.backend_used == "bm25":
        assert r.backend_reason.startswith("silent_fallback_")
        assert r.loaded is True  # bm25 should have loaded


# ---------------------------------------------------------------- #
# 4. bm25_fallback is explicit
# ---------------------------------------------------------------- #

def test_bm25_fallback_explicit_records_reason():
    from policy_copilot.retrieve.retriever import Retriever
    r = Retriever(backend="bm25_fallback")
    assert r.backend_requested == "bm25_fallback"
    assert r.backend_used == "bm25"
    assert r.backend_reason == "explicit_fallback"
    assert r.loaded is True


# ---------------------------------------------------------------- #
# 5. run_eval --help accepts new backend choices
# ---------------------------------------------------------------- #

def test_run_eval_help_lists_new_backends():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_eval.py"), "--help"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    # argparse renders choices as {dense,bm25,hybrid,bm25_fallback}
    out = proc.stdout
    for choice in ("dense", "bm25", "hybrid", "bm25_fallback"):
        assert choice in out, f"--backend choice missing from help: {choice}"


# ---------------------------------------------------------------- #
# 6. unknown backend rejected
# ---------------------------------------------------------------- #

def test_unknown_backend_rejected():
    from policy_copilot.retrieve.retriever import Retriever
    with pytest.raises(ValueError):
        Retriever(backend="nonsense_backend")
