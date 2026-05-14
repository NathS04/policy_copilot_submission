# Claim-Evidence Map

Maps major claims made in the dissertation report to their backing artifacts in the repository.

## Core Performance Claims

| Claim | Report Section | Backing Artifact | Verification |
|-------|---------------|------------------|--------------|
| B3 achieves 0% ungrounded rate | Section 4.2, Table 4.2 | `results/runs/b3_generative_bm25_fallback_final/summary.json` → `ungrounded_rate: 0.0` | `python -c "import json; d=json.load(open('results/runs/b3_generative_bm25_fallback_final/summary.json')); print(d['ungrounded_rate'])"` |
| B3 abstention accuracy = 94.1% | Section 4.2, Table 4.2 | `results/runs/b3_generative_bm25_fallback_final/summary.json` → `abstention_accuracy: 0.9412` | Same file |
| B1 answer rate = 100% | Section 4.2, Table 4.2 | `results/runs/b1_generative_final/summary.json` → `answer_rate: 1.0` | Same file |
| Critic macro precision / recall / F1 = 93.3% / 95.2% / 93.8% on the 50-snippet labelled suite | Section 4.7, Table 4.6 | `results/tables/critic_summary.csv` | `python scripts/run_critic_eval.py --run_name critic_heuristic_final --mode heuristic` |

## Architecture Claims

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Three-baseline evaluation ladder (B1/B2/B3) | Section 2.6 | `scripts/run_eval.py` supports `--baseline b1/b2/b3/all` |
| Ablation support | Section 2.6 / 4.6 | `scripts/run_eval.py` supports `--no_rerank`, `--no_verify`, `--no_contradictions` |
| Cross-encoder reranking | Section 3.3 | `src/policy_copilot/rerank/reranker.py` using `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Jaccard-based claim verification | Section 3.5 | `src/policy_copilot/verify/citation_check.py` |
| Confidence-gated abstention | Section 3.5 | `src/policy_copilot/verify/abstain.py` |
| Contradiction detection | Section 3.5 | `src/policy_copilot/verify/contradictions.py` |
| L1-L6 critic taxonomy | Section 3.6 | `src/policy_copilot/critic/labels.py`, `src/policy_copilot/critic/critic_agent.py` |
| Hybrid retrieval (RRF) | Section 3.3 | `src/policy_copilot/retrieve/hybrid.py` |
| Multi-mode UI (6 views) | Section 3.7 | `src/policy_copilot/ui/streamlit_app.py` (Ask, Audit Trace, Critic Lens, Experiment Explorer, Reviewer Mode, Help & Guide) |

## Testing Claims

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Automated test suite (200 collected: 199 pass, 1 conditionally skipped) | Section 3.9, Appendix B.7.1, B.9 | `tests/` directory, `pyproject.toml` |
| Offline reproduction | Section 2.6 / Appendix B.7 | `scripts/reproduce_offline.py` |
| Online reproduction | Section 2.6 / Appendix B.7 | `scripts/reproduce_online.py` |

## Evaluation Methodology Claims

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Golden set: 63 queries (36 answerable, 17 unanswerable, 10 contradiction) | Section 2.7 / Table 4.1 | `eval/golden_set/golden_set.csv` |
| Dev/test split (19 dev, 44 test) | Section 2.7 / Table 4.1 | CSV `split` column |
| Independent peer reviewer evaluation (n = 6 reviewers, 14–18 April 2026) on a structured sub-sample of the golden set | Section 4.10 / Table 4.9 | `docs/evidence/human_eval/anonymised_scores.csv`, `summary_stats.csv`, `thematic_summary.md`; participant materials in `eval/human_eval/` |
| Bootstrapped 95% confidence intervals (n = 63, 2,000 resamples, seed = 42) | Section 4.12 / Table 4.11 | `scripts/compute_bootstrap_ci.py`; output in `results/tables/statistical_confidence.csv` |

## Auditability and Evaluation Claims (added in Final Maximiser phase)

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Risk audit table with 10 failure modes | Section 2.5 + `docs/risk_audit_table.md` | `docs/risk_audit_table.md` |
| Conclusions and reflection (mapped to marking criterion) | Chapter 5 (§5.1 Conclusions, §5.2 Limitations, §5.3 Future Work, §5.4 Reflection) | `docs/report/Final_Report_Nathaniel_Sebastian_201715051.md` |
| 8-category failure-mode taxonomy with per-baseline counts | Section 4.8 | `eval/analysis/error_taxonomy.md`, `scripts/classify_errors.py`, `results/tables/failure_taxonomy.csv` |
| 5-axis auditability rubric (evidence relevance, citation faithfulness, abstention correctness, contradiction correctness, failure mode) | Section 2.6 | `eval/rubrics/auditability_rubric.md`, `scripts/compute_auditability_scores.py`, `results/tables/auditability_scores.csv` |
| Ablation comparison with metric deltas | Section 4.6 / Table 4.5 | `scripts/compare_ablations.py`, `results/tables/ablation_comparison.csv` |
| Token/cost reporting schema and pipeline | Section 4.9 | `schemas.py:TokenUsage`, `chat_orchestrator.py`, `run_eval.py` |
| Objective slice evaluation (16 deterministic queries) | Section 4.1 | `scripts/eval_objective_slice.py`, `results/tables/objective_slice_results.csv` |
| B1 dominant failure = missed retrieval, B2 = wrong claim-evidence link, B3 = abstention error | Section 4.8 | `results/tables/failure_taxonomy.csv` |

## Claims NOT Made (important for honesty)

- No claim of multi-model evaluation (only one OpenAI generator was tested under the BM25 fallback configuration).
- Independent peer reviewers were Computer Science peers, not policy or compliance domain experts; this is recorded as a limitation in §5.2 (L5).
- Primary benchmark is the synthetic 63-query golden set; a small extractive-only public-guidance transfer test (§4.11) is the only check on non-author-written content, and full transfer to messier real corpora is not demonstrated.
- No deployment or user study; the system has not been used by real reviewers under operational conditions.
- No claim of automated faithfulness scoring (e.g. RAGAS) — grounding is approximated via support rate and citation metrics, with the limitations documented in §4.4 and §5.2.
