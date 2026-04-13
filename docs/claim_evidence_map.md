# Claim-Evidence Map

Maps major claims made in the dissertation report to their backing artifacts in the repository.

## Core Performance Claims

| Claim | Report Section | Backing Artifact | Verification |
|-------|---------------|------------------|--------------|
| B3 achieves 0% ungrounded rate | Section 4.2, Table 4.2 | `results/runs/b3_generative_bm25_fallback_final/summary.json` → `ungrounded_rate: 0.0` | `python -c "import json; d=json.load(open('results/runs/b3_generative_bm25_fallback_final/summary.json')); print(d['ungrounded_rate'])"` |
| B3 abstention accuracy = 94.1% | Section 4.2, Table 4.2 | `results/runs/b3_generative_bm25_fallback_final/summary.json` → `abstention_accuracy: 0.9412` | Same file |
| B1 answer rate = 100% | Section 4.2, Table 4.2 | `results/runs/b1_generative_final/summary.json` → `answer_rate: 1.0` | Same file |
| Critic macro precision = 93.7% | Section 4.6 | Critic eval output (reported in text) | `python scripts/run_critic_eval.py --mode heuristic` |

## Architecture Claims

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Three-baseline evaluation ladder (B1/B2/B3) | Section 2.4 | `scripts/run_eval.py` supports `--baseline b1/b2/b3/all` |
| Ablation support | Section 2.4 | `scripts/run_eval.py` supports `--no_rerank`, `--no_verify`, `--no_contradictions` |
| Cross-encoder reranking | Section 3.4 | `src/policy_copilot/rerank/reranker.py` using `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Jaccard-based claim verification | Section 3.5 | `src/policy_copilot/verify/citation_check.py` |
| Confidence-gated abstention | Section 3.5 | `src/policy_copilot/verify/abstain.py` |
| Contradiction detection | Section 3.5 | `src/policy_copilot/verify/contradictions.py` |
| L1-L6 critic taxonomy | Section 3.6 | `src/policy_copilot/critic/labels.py`, `src/policy_copilot/critic/critic_agent.py` |
| Hybrid retrieval (RRF) | Section 3.3 | `src/policy_copilot/retrieve/hybrid.py` |
| Multi-mode UI (5 views) | Section 3.7 | `src/policy_copilot/ui/streamlit_app.py` (Ask, Audit Trace, Critic Lens, Experiment Explorer, Reviewer Mode) |

## Testing Claims

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Automated test suite | Section 3.8 | `tests/` directory, `pytest` configuration in `pyproject.toml` |
| Offline reproduction | Section 2.6 | `scripts/reproduce_offline.py` |
| Online reproduction | Section 2.6 | `scripts/reproduce_online.py` |

## Evaluation Methodology Claims

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Golden set: 63 queries (36 answerable, 17 unanswerable, 10 contradiction) | Section 2.3 | `eval/golden_set/golden_set.csv` |
| Dev/test split | Section 2.3 | CSV `split` column: 19 dev, 44 test |
| Human evaluation on 20 queries | Section 4.8b | `eval/human_eval/README.md`, report Table 4.7b |
| Bootstrapped confidence intervals | Section 4.8c | Report Table 4.7c |

## Auditability and Evaluation Claims (added in Final Maximiser phase)

| Claim | Report Section | Backing Artifact |
|-------|---------------|------------------|
| Risk audit table with 10 failure modes | Section 6.1 / Appendix | `docs/risk_audit_table.md` |
| 8-category failure-mode taxonomy with per-baseline counts | Section 4.8 | `eval/analysis/error_taxonomy.md`, `scripts/classify_errors.py`, `results/tables/failure_taxonomy.csv` |
| 5-axis auditability rubric (evidence relevance, citation faithfulness, abstention correctness, contradiction correctness, failure mode) | Section 4.1 | `eval/rubrics/auditability_rubric.md`, `scripts/compute_auditability_scores.py`, `results/tables/auditability_scores.csv` |
| Ablation comparison with metric deltas | Section 4.6 | `scripts/compare_ablations.py`, `results/tables/ablation_comparison.csv` |
| Token/cost reporting schema and pipeline | Section 4.8a | `schemas.py:TokenUsage`, `chat_orchestrator.py`, `run_eval.py` |
| B1 dominant failure = missed retrieval, B2 = wrong claim-evidence link, B3 = abstention error | Section 4.8 | `results/tables/failure_taxonomy.csv` |

## Claims NOT Made (important for honesty)

- No claim of multi-model evaluation (only OpenAI tested)
- No claim of independent human raters (single rater acknowledged)
- No claim of real-world corpus testing (synthetic corpus acknowledged)
- No claim of deployment or user study
- No claim of automated faithfulness scoring (e.g. RAGAS) — grounding approximated via support rate and citation metrics
