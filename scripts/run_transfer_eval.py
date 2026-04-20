"""Run B3-Extractive against the Public Guidance Transfer Stress Test.

This is a thin wrapper over scripts/run_eval.py that:

  1. Points ``settings.PROCESSED_DATA_DIR`` (and the BM25 retriever's
     paragraphs.jsonl path) at ``data/public_transfer_corpus/processed/``
     instead of the default synthetic corpus.
  2. Uses ``eval/golden_set/public_transfer_set.csv`` as the golden set.
  3. Forces ``--mode extractive --backend bm25`` so no LLM API key is
     required (and so the run is deterministic, since extractive mode
     just returns the top-1 reranked / BM25 paragraph verbatim).
  4. Writes results under ``results/runs/b3_extractive_public_transfer/``.

This produces the supplementary evidence used in Section 4.11 of the
dissertation (Public Guidance Transfer Stress Test). The corpus is OGL
v3.0-licensed material from NCSC, ICO, and ACAS; provenance is recorded
in ``data/public_transfer_corpus/provenance.csv`` and reproduced in
Appendix B.11.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "src"))


def main() -> int:
    # 1. Override settings to point at the public transfer corpus.
    from policy_copilot.config import settings
    transfer_corpus = HERE / "data" / "public_transfer_corpus" / "processed"
    settings.PROCESSED_DATA_DIR = transfer_corpus
    settings.CORPUS_DIR = transfer_corpus
    settings.CORPUS_JSONL = transfer_corpus / "paragraphs.jsonl"

    # 2. Force CLI flags appropriate for the transfer test.
    sys.argv = [
        "run_eval.py",
        "--baseline", "b3",
        "--run_name", "b3_extractive_public_transfer",
        "--golden_set", str(HERE / "eval" / "golden_set" / "public_transfer_set.csv"),
        "--split", "test",
        "--mode", "extractive",
        "--backend", "bm25",
        "--allow_no_key",
        "--force",
    ]

    # 3. Hand off to the existing runner.
    import scripts.run_eval as run_eval  # noqa: E402
    return run_eval.main()


if __name__ == "__main__":
    raise SystemExit(main())
