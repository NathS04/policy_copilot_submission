# Claim → Evidence Checklist

This file maps the substantive claims in Chapters 4 and 5 of the
dissertation to the artefacts in the repository that evidence them.
Claims are paraphrased for brevity; the report is the authoritative
wording.

## Chapter 4 — Results, Evaluation and Discussion

| § | Claim (paraphrased) | Evidence file(s) |
| :--- | :--- | :--- |
| 4.2 | B3-Generative answer rate 25.0%, abstention accuracy 94.1%, ungrounded rate 0.0% | `results/runs/b3_generative_bm25_fallback_final/summary.json` |
| 4.2 | B2-Generative answer rate 83.3%, abstention accuracy 76.5%, evidence recall@5 73.9% | `results/runs/b2_generative_bm25_fallback_final/summary.json` |
| 4.2 | B1-Generative answer rate 100%, abstention accuracy 0% | `results/runs/b1_generative_final/summary.json` |
| 4.3 | B2 and B3 retrieval metrics identical under BM25 fallback | `results/tables/run_summary.csv` |
| 4.4 | Per-claim ungrounded rate 12% before verification, 4% after; citation precision 78%→94% | Section 4.4 narrative; intermediate metrics in `outputs.jsonl` claim-level fields |
| 4.5 | Operating curve over support-rate threshold τ ∈ [0.0, 1.0]; knee at τ ≈ 0.65 | `results/tables/threshold_sweep.csv` (produced by `scripts/sweep_abstention.py`) |
| 4.6 | Reranker is the largest single contributor in ablations | Section 4.6 Table 4.5; ablation row notes are dev-phase estimates clearly labelled as such |
| 4.7 | Critic Mode macro F1 84.8% | `tests/test_critic.py`; per-pattern numbers in §4.7 |
| 4.8 | Error taxonomy: over-abstention dominates B3 failures | Section 4.8 Table 4.7 |
| 4.9 | B3 P95 latency 4.9s on consumer hardware | Section 4.9 Table 4.8 |
| 4.10 | Independent reviewer evaluation, n = 6 peer reviewers, 14-18 April 2026 | `docs/evidence/human_eval/anonymised_scores.csv`, `summary_stats.csv`, `thematic_summary.md` |
| 4.11 | B3-Extractive on public guidance corpus: 91.7% answer rate, 100% citation precision, 0% ungrounded rate | `results/runs/b3_extractive_public_transfer/summary.json` |
| 4.11 | OGL-licensed corpus (NCSC + ICO + ACAS), 8 docs, 249 paragraphs | `data/public_transfer_corpus/provenance.csv` and `processed/paragraphs.jsonl` |
| 4.12 | Bootstrapped 95% CIs for B3 headline metrics | Section 4.12 Table 4.11 (n=63, 2,000 resamples, seed=42) |
| 4.13 | Objective achievement summary | Section 4.13 Table 4.12 |

## Chapter 5 — Conclusions and Reflection

| § | Claim (paraphrased) | Evidence file(s) |
| :--- | :--- | :--- |
| 5.1 | Cross-encoder reranking is the highest-leverage reliability layer | Section 4.6 ablations; `results/tables/run_summary.csv` |
| 5.2 (L1) | Synthetic corpus is the primary benchmark; safety properties stress-tested on public corpus | `results/runs/b3_extractive_public_transfer/summary.json` |
| 5.2 (L2) | Golden set = 63 queries (44 test, 19 dev) | `eval/golden_set/golden_set.csv` |
| 5.2 (L5) | Independent reviewer evaluation is small (n = 6), author-facilitated, non-domain-expert | `docs/evidence/human_eval/anonymised_scores.csv` |

## Software-engineering claims

| Claim (paraphrased) | Evidence |
| :--- | :--- |
| 188 automated tests, 1 conditionally skipped, all pass | `pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py` per `INSTRUCTIONS_FOR_EVALUATOR.md` |
| Reproducible offline (BM25, no API key) | `scripts/reproduce_offline.py` |
| Reproducible online (dense + LLM) | `scripts/reproduce_online.py` |
| Pure replay of abstention thresholds | `scripts/sweep_abstention.py` |
| Honest figures (NaN not 0.0 for missing) | `eval/analysis/make_figures.py --strict` |

## Ethics and process claims

| Claim (paraphrased) | Evidence |
| :--- | :--- |
| Independent reviewer evaluation under voluntary informed consent | `docs/evidence/human_eval/consent_text.md`, `participant_info.md` |
| No personal data retained | Inspect `docs/evidence/human_eval/anonymised_scores.csv` (only P1-P6 + role tag + Likert scores) |
| OGL-licensed public corpus | `data/public_transfer_corpus/provenance.csv` |
| AI-use disclosed under University of Leeds Generative AI policy (Amber) | Appendix B.5 of the report; commit history in `git log` |
