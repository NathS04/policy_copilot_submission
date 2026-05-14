# Evidence Capture Guide

This document records how each artefact under `docs/evidence/` (and its
back-references in `results/`, `eval/`, `data/`) was produced, and how
each can be regenerated. Every reproduction command assumes:

- Project root checkout
- A clean `python3 -m venv .venv && source .venv/bin/activate`
- One of: `pip install -e ".[dev]"` (offline / BM25) or
  `pip install -e ".[ml,dev]"` (online / dense + LLM)
- For online runs: `OPENAI_API_KEY` set in `.env`

The standard reference environment is the offline / BM25 path. The
online path is required only for B1-Generative and B2/B3-Generative
end-to-end runs against the dense backend.

## Independent reviewer evaluation (Section 4.10)

| Artefact | Source | Reproducibility |
| :--- | :--- | :--- |
| `human_eval/anonymised_scores.csv` | Six volunteer peer reviewers, 14-18 April 2026, distributed via Google Form. Anonymisation at collection time: only `P1`-`P6` + role tag retained. | Not regenerable from code: this is a one-shot evaluation. The Google Form export is mirrored here with all participant identifiers stripped. |
| `human_eval/summary_stats.csv` | Per-axis mean / SD / min / max computed from `anonymised_scores.csv`. | `python -c "import csv,statistics; ..."` (or use the inline computation in `scripts/sweep_abstention.py` style). |
| `human_eval/thematic_summary.md` | Five themes coded from optional one-line comments. No verbatim quotes retained. | Not regenerable: thematic coding was performed by the author after the evaluation closed. |
| `human_eval/rubric.md` | Formal rubric definition (1-5 Likert, five axes) given to participants. | Authored once; mirrored from `eval/human_eval/rubric.md`. |
| `human_eval/consent_text.md`, `participant_info.md` | Information sheet and consent wording distributed to participants. | Authored once; mirrored from `eval/human_eval/`. |

The aggregate numbers in Section 4.10 Table 4.9 and the per-category
breakdown in Appendix B.10 are computed directly from
`anonymised_scores.csv` plus the per-category split.

## Public Guidance Transfer Stress Test (Section 4.11)

| Artefact | Source | Reproducibility |
| :--- | :--- | :--- |
| `data/public_transfer_corpus/raw/` | Six pages downloaded from NCSC, ICO, and ACAS (all OGL v3.0). | `python scripts/download_public_corpus.py` |
| `data/public_transfer_corpus/processed/paragraphs.jsonl` | Same chunking pipeline as the synthetic corpus. | `python scripts/ingest_public_corpus.py` |
| `data/public_transfer_corpus/provenance.csv` | URL, title, license, access date, content hash per source. | Re-emitted by `download_public_corpus.py`; idempotent. |
| `eval/golden_set/public_transfer_set.csv` | 20 queries (12 answerable, 4 unanswerable, 4 ambiguous) annotated by inspection. | Authored once; gold paragraph IDs verified by spot-check against `paragraphs.jsonl`. |
| `results/runs/b3_extractive_public_transfer/summary.json` | B3-Extractive end-to-end run on the public corpus, BM25 backend, no LLM. | `python scripts/run_transfer_eval.py` |

## Headline runs (Section 4.2 - 4.6)

| Run | Reproducibility |
| :--- | :--- |
| `results/runs/b1_generative_final/` | `python scripts/run_eval.py --baseline b1 --mode generative --backend dense` (requires API key) |
| `results/runs/b2_generative_bm25_fallback_final/` | `python scripts/run_eval.py --baseline b2 --mode generative --backend dense` (BM25 used after dense-index fallback) |
| `results/runs/b3_generative_bm25_fallback_final/` | `python scripts/run_eval.py --baseline b3 --mode generative --backend dense` |
| `results/runs/b3_test_extractive_bm25_*` | `python scripts/run_eval.py --baseline b3 --mode extractive --backend bm25` |

## Threshold sweep (Section 4.5)

| Artefact | Reproducibility |
| :--- | :--- |
| `results/tables/threshold_sweep.csv` | `python scripts/sweep_abstention.py` (replays from existing `b3_generative_bm25_fallback_final/outputs.jsonl`; no LLM cost). |
| `docs/report/figures/fig_tradeoff.png` | `python eval/analysis/make_figures.py --out_fig_dir docs/report/figures` |
| `results/tables/bm25_threshold_retuning.csv`, `results/tables/bm25_threshold_retuning_summary.json`, `docs/report/figures/fig_bm25_retuned_operating_point.png` | `python scripts/analyse_bm25_threshold_retuning.py` (also a replay over `outputs.jsonl`; adds a per-τ response-level Ungrounded Rate column and selects an operating point under the dual safety constraints; cross-checks the reconstructed τ = 0.80 row against `summary.json` before writing artefacts; no LLM cost). |

## Figures (Chapter 1, 2, 4)

| Figure | Reproducibility |
| :--- | :--- |
| Figure 1.1 PRISMA, Figure 2.1 Gantt, Figure 2.2 architecture | `python scripts/generate_diagrams.py` |
| Figures 4.1 - 4.4 | `python eval/analysis/make_figures.py --out_fig_dir docs/report/figures` |

## Tests (Section 3.8 / Appendix B.7.1)

| Claim | Reproducibility |
| :--- | :--- |
| 292 collected: 290 passed, 2 conditionally skipped | `pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py` |

## Report build (Appendix B.7.2)

| Claim | Reproducibility |
| :--- | :--- |
| Final PDF builds via Markdown → DOCX → LibreOffice | `python scripts/build_report.py` (iterative pagemap; converges in 2-3 passes) |

## Out of scope

The following are not reproducible from code in this repository because
they are either one-shot human-collected data or proprietary
infrastructure:

- Independent reviewer evaluation results (`anonymised_scores.csv`):
  one-shot human study; the Google Form export is the source of truth.
- LLM API responses: vary with model versions; the recorded
  `outputs.jsonl` files are the canonical artefacts.
- Public-guidance source HTML: NCSC / ICO / ACAS pages may be edited
  in place; the cached `data/public_transfer_corpus/raw/` text and
  content hashes in `provenance.csv` are the canonical record of what
  was used.
