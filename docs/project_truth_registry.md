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
| Reviewer rubric scoring | Round 2: 6 reviewers x 20 queries x 5 axes |
| Multi-rater agreement | Krippendorff alpha computed per axis; see `docs/evidence/human_eval/inter_rater_agreement.md` |
| Independent raters | Yes — 6 independent reviewers (R1-R6) in Round 2 |

## Research Pack — Count Hierarchy (Authoritative)

Two complementary literature flows are reported. Both are valid and they are not contradictory.

| Tier | Count | Source |
|------|-------|--------|
| **Strict scholarly review (Report Chapter 1 PRISMA)** | | |
| Raw database hits (cross-database, w/ duplicates) | 584 | Report §1.3 |
| After deduplication | 472 | Report §1.3 |
| Full-text assessed | 154 | Report §1.3 |
| **Core peer-reviewed studies included** | **38** | Report Chapter 1 |
| **Broader research pack (literature matrix)** | | |
| Unique title-level candidates (matrix flow) | ~120 | `search_strategy.md` |
| Citation-chain additions | ~55 | `search_strategy.md` |
| **All sources in literature matrix** | **105** | `docs/research/literature_matrix.md` |
| Tier 1 venues (matrix) | 59 | literature_matrix.md |
| Tier 2 venues (matrix) | 27 | literature_matrix.md |
| Tier 3 / practitioner (matrix) | 19 | literature_matrix.md |
| Direct comparator systems | 10 | `docs/research/comparator_matrix.md` / Appendix B.8 |
| Topic clusters | 10 (C1–C10) | literature_matrix.md, taxonomy |
| Criticising sources (matrix) | 16 | literature_matrix.md |

## UI Views

| View | Purpose | Service dependency |
|------|---------|-------------------|
| Ask | GPT-style chat with inline citations | `ChatOrchestrator` |
| Audit Trace | Claim-by-claim verification dossier | `AuditReportService` |
| Critic Lens | L1-L6 policy language analysis | `critic_agent.detect_heuristic` |
| Experiment Explorer | Browse and compare evaluation runs | `RunInspector` |
| Reviewer Mode | Human rubric scoring with export | `ReviewerService` |
| Help & Guide | Getting started, mode guide, glossary, FAQ, accessibility | Static content (no service) |

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
| Total test files | 39 | `tests/` directory |
| Total test cases | 195 | `pytest -q` output |
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
- No claim of real-world corpus testing (synthetic corpus acknowledged; Public Guidance Transfer Stress Test is a stress probe, not a full transfer evaluation)
- No claim of deployment or user study
