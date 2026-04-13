# Project Truth Registry

Single source of truth for all critical counts, claims, and definitions.
Any contradiction with this file in other documents is a bug.

## Golden Set

| Fact | Value | Source |
|------|-------|--------|
| Total queries | 63 | `eval/golden_set/golden_set.csv` |
| Answerable | 36 | CSV `category` column |
| Unanswerable | 17 | CSV `category` column |
| Contradiction | 10 | CSV `category` column |
| Dev split | 19 | CSV `split` column |
| Test split | 44 | CSV `split` column |
| Frozen version | `golden_set_frozen_v1.csv` | `eval/golden_set/` |

## Baselines

| Baseline | Name | Description |
|----------|------|-------------|
| B1 | Prompt-only LLM | No retrieval; measures hallucination baseline |
| B2 | Naive RAG | Top-k=5 evidence, no reranking or abstention |
| B3 | Full system | Reranking + confidence-gated abstention + per-claim citation verification + contradiction surfacing |

## Key Metrics (from `results/runs/*/summary.json`)

| Metric | B1 | B3 | Source |
|--------|-----|-----|--------|
| Answer rate | 100% | ~25% | summary.json `answer_rate` |
| Ungrounded rate | N/A | 0.0% | summary.json `ungrounded_rate` |
| Abstention accuracy | N/A | 94.12% (0.9412) | summary.json `abstention_accuracy` |
| Critic macro precision | — | 93.7% | `run_critic_eval.py --mode heuristic` |

## Human Evaluation Status

| Fact | Status |
|------|--------|
| Single-rater rubric scoring | Exercised (20 queries) |
| Multi-rater agreement (kappa) | Future work only — tooling exists but not exercised |
| Independent raters | No — single rater acknowledged |

## Research Pack

| Fact | Value | Source |
|------|-------|--------|
| Total sources in literature matrix | 105 | `docs/research/literature_matrix.md` summary table |
| Tier 1 venues | 59 | literature_matrix.md |
| Tier 2 venues | 27 | literature_matrix.md |
| Tier 3 / practitioner | 19 | literature_matrix.md |
| Initial shortlist (database search) | 48 | search_strategy.md |
| Citation chaining additions | ~52 | search_strategy.md |
| Direct comparator systems | 10 | `docs/research/comparator_matrix.md` |
| Topic clusters | 10 (C1-C10) | literature_matrix.md, taxonomy |
| Criticising sources | 16 | literature_matrix.md |

## UI Views

| View | Purpose | Service dependency |
|------|---------|-------------------|
| Ask | GPT-style chat with inline citations | `ChatOrchestrator` |
| Audit Trace | Claim-by-claim verification dossier | `AuditReportService` |
| Critic Lens | L1-L6 policy language analysis | `critic_agent.detect_heuristic` |
| Experiment Explorer | Browse and compare evaluation runs | `RunInspector` |
| Reviewer Mode | Human rubric scoring with export | `ReviewerService` |

## Provenance Behaviour

| Fact | Truth |
|------|-------|
| `backend_requested` vs `backend_used` | Tracked per query in `QueryResult` |
| `verify_artifacts.py --strict` | Fails if `backend_requested != backend_used` (unless `--allow_backend_mismatch`) |
| Offline reproduction backend | BM25 (lexical), extractive mode |
| Online reproduction backend | Dense (FAISS), generative mode |

## Test Suite

| Fact | Value | Source |
|------|-------|--------|
| Total test files | 38 | `tests/` directory |
| Total test cases | 186 | `pytest -q` output |
| Conditionally skipped | 1 | FAISS-dependent test |

## Evaluation Artefacts (added in Final Maximiser phase)

| Artefact | File | Status |
|----------|------|--------|
| Risk audit table | `docs/risk_audit_table.md` | Complete — 10 failure modes with detection, mitigation, residual risk |
| Failure-mode taxonomy | `eval/analysis/error_taxonomy.md` + `scripts/classify_errors.py` | Complete — 8 categories, automated classification, per-baseline CSV |
| Auditability rubric | `eval/rubrics/auditability_rubric.md` + `scripts/compute_auditability_scores.py` | Complete — 5-axis rubric with automated scoring |
| Ablation comparison | `scripts/compare_ablations.py` | Complete — side-by-side delta table across baselines |
| Token/cost reporting | `schemas.py:TokenUsage` + `chat_orchestrator.py` + `run_eval.py` | Schema and pipeline wired; shipped final runs predate this feature so contain no token data; future runs will capture tokens per query |
| Objective slice evaluation | `eval/golden_set/golden_set.csv` (objective_slice column) + `scripts/eval_objective_slice.py` | Complete — 16 deterministically-checkable queries tagged; evaluator produces `objective_slice_results.csv` |
| Demo storyline scripts | `docs/demo_scripts.md` | Complete — 3 viva demo journeys documented |
| Failure taxonomy CSV | `results/tables/failure_taxonomy.csv` | Generated from shipped runs |
| Auditability scores CSV | `results/tables/auditability_scores.csv` | Generated from shipped runs |
| Ablation comparison CSV | `results/tables/ablation_comparison.csv` | Generated from shipped runs |

## Claims NOT Made

- No claim of multi-model evaluation (only OpenAI tested)
- No claim of independent human raters (single rater acknowledged)
- No claim of real-world corpus testing (synthetic corpus acknowledged)
- No claim of deployment or user study
- No claim of kappa agreement (tooling exists, not exercised)
