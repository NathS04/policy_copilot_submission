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
| 5.2 (L1) | Synthetic corpus is the primary benchmark; conservative extractive behaviour checked on a small public corpus | `results/runs/b3_extractive_public_transfer/summary.json` |
| 5.2 (L2) | Golden set = 63 queries (44 test, 19 dev) | `eval/golden_set/golden_set.csv` |
| 5.2 (L5) | Independent reviewer evaluation is small (n = 6), author-facilitated, non-domain-expert | `docs/evidence/human_eval/anonymised_scores.csv` |

## Software-engineering claims

| Claim (paraphrased) | Evidence |
| :--- | :--- |
| 194 collected tests under the documented evaluator command: 193 pass, 1 conditionally skipped | `pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py` per `INSTRUCTIONS_FOR_EVALUATOR.md` |
| Reproducible offline (BM25, no API key) | `scripts/reproduce_offline.py` |
| Reproducible online (dense + LLM) | `scripts/reproduce_online.py` |
| Pure replay of abstention thresholds | `scripts/sweep_abstention.py` |
| Honest figures (NaN not 0.0 for missing) | `eval/analysis/make_figures.py` |

`results/manifest.json` records `"strict": false`. This is intentional under the offline-only verification path: the manifest covers the retained artefacts and the offline-safe runs, without requiring an API-enabled regeneration of generative outputs. Missing or unavailable online-generative artefacts are preserved explicitly rather than silently filled.

## Claim → artefact → command (compact)

For every report claim, this table maps the artefact that backs it and the exact command an examiner can run to regenerate that artefact from a fresh install.

| Report claim | Evidence file(s) | Reproduction command |
| :--- | :--- | :--- |
| B3-Generative response-level headline metrics | `results/runs/b3_generative_bm25_fallback_final/summary.json`; `results/tables/run_summary.csv` | `python scripts/verify_artifacts.py` |
| B3-Extractive synthetic headline metrics (89% / 100% / 0%) | `results/runs/b3_extractive_final/summary.json`; `results/tables/run_summary.csv` | `python scripts/run_eval.py --baseline b3 --mode extractive --backend bm25 --split test --run_name b3_extractive_final --allow_no_key` |
| B1 / B2 / B3 baseline comparison | `results/tables/run_summary.csv`; `results/figures/fig_baselines.png` | `python scripts/reproduce_offline.py` |
| Public-transfer corpus provenance and OGL licensing | `data/public_transfer_corpus/provenance.csv` | `python scripts/download_public_corpus.py` |
| Public-transfer extractive results | `results/runs/b3_extractive_public_transfer/summary.json`; `eval/public_transfer/failure_taxonomy.csv` | `python scripts/run_transfer_eval.py` |
| Independent reviewer evaluation | `docs/evidence/human_eval/summary_stats.csv`; `inter_rater_agreement.md` | `python scripts/compute_human_eval.py` |
| Adversarial probe (Appendix B.12) | `eval/adversarial/adversarial_summary.csv` | `python scripts/run_adversarial.py` |
| Audit exports (the "audit-ready" claim) | `docs/evidence/verification/audit_export_*.md` | `python scripts/build_audit_exports.py` |
| Figures used in Chapter 4 | `results/figures/fig_*.png` | `python eval/analysis/make_figures.py` |
| Clean submission ZIP | `Final_Submission_Nathaniel_Sebastian_201715051.zip` (sibling of project) | `python scripts/build_clean_submission_zip.py` |
| Fresh-install verification log | [`docs/evidence/verification/fresh_install_log.md`](verification/fresh_install_log.md) | Re-run all of the above in a fresh venv and paste the summary back in |
| Vertical-slice case study | [`docs/evidence/verification/vertical_slice_case_study.md`](verification/vertical_slice_case_study.md) | One-page walkthrough of an answered, an abstained, and a contradiction-surfaced query, pulled verbatim from the three existing audit exports |

Every headline metric in Chapter 4 maps to a concrete repository artefact so that the result can be audited rather than taken on trust.

For a short walkthrough of one answerable query, one unanswerable query, and one contradiction probe, see [`docs/evidence/verification/vertical_slice_case_study.md`](verification/vertical_slice_case_study.md).

## Ethics and process claims

| Claim (paraphrased) | Evidence |
| :--- | :--- |
| Independent reviewer evaluation under voluntary informed consent | `docs/evidence/human_eval/consent_text.md`, `participant_info.md` |
| No personal data retained | Inspect `docs/evidence/human_eval/anonymised_scores.csv` (only P1-P6 + role tag + Likert scores) |
| OGL-licensed public corpus | `data/public_transfer_corpus/provenance.csv` |
| AI-use disclosed under University of Leeds Generative AI policy (Amber) | Appendix B.5 of the report; commit history in `git log` |
