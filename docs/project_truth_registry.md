# Project Truth Registry

This file summarises the final package state. It should be checked against
the final report and evidence pack; contradictions are bugs in whichever
file is stale.

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

### B1 / B2 / B3-Generative (synthetic, all-split, generative)

| Metric | B1 | B2 | B3-Generative | Source |
|--------|-----|-----|-----|--------|
| Answer rate | 100% | 83.33% | 25.0% | summary.json `answer_rate` |
| Abstention accuracy | 0.0% | 76.47% | 94.12% | summary.json `abstention_accuracy` |
| Response-level ungrounded rate | N/A | N/A | 0.0% (after `min_support_rate` gate; not a claim that the LLM never produced unsupported text) | summary.json `ungrounded_rate` |
| Evidence Recall@5 | N/A | 73.91% | 73.91% (BM25 fallback; dev-phase dense ≈ 85%) | summary.json `evidence_recall` |

### B3-Extractive (synthetic, test-split, extractive, BM25)

| Metric | Value | Source |
|--------|-------|--------|
| Answer rate | 88% (~89%) | `results/runs/b3_extractive_final/summary.json` |
| Citation precision | 100% (mechanical: response is the cited paragraph) | summary.json `citation_precision` |
| Ungrounded rate | 0% (mechanical in Extractive Mode) | summary.json `ungrounded_rate` |
| Abstention accuracy | 50% | summary.json `abstention_accuracy` |
| Evidence Recall@5 | 73.4% | summary.json `evidence_recall_at_5` |

### Critic Mode

| Metric | Value | Source |
|--------|-------|--------|
| Macro precision | 93.7% | `run_critic_eval.py --mode heuristic` |
| Macro recall | 78.5% | as above |
| Macro F1 | 84.8% (below 85% FR6 target by 0.2 pp) | as above |

## Human Evaluation Status

| Fact | Status |
|------|--------|
| Reviewer rubric scoring | Round 1 aggregate (P1-P6) + Round 2 per-query (R1-R6) |
| Round 2 sample | 6 reviewers × 20 queries × 5 axes = 120 ratings per axis |
| Multi-rater agreement | Krippendorff α per axis; see `docs/evidence/human_eval/inter_rater_agreement.md` |
| Independent raters | Yes — 6 independent reviewers (CS peers, not domain experts; author-facilitated, not blinded) |
| Scope | Small low-risk peer-review check, not a formal user study |

## Public Guidance Transfer Stress Test

| Fact | Value | Source |
|------|-------|--------|
| Source organisations | NCSC, ICO, ACAS | `data/public_transfer_corpus/provenance.csv` |
| Documents | 8 | `data/public_transfer_corpus/README.md` |
| Paragraphs | 249 | as above |
| Query set | 20 queries (12 answerable / 4 unanswerable / 4 ambiguous) | `eval/golden_set/public_transfer_set.csv` |
| Mode tested | Extractive-only | `results/runs/b3_extractive_public_transfer/summary.json` |
| Licence | Open Government Licence v3.0 with attribution | `provenance.csv` |
| Used to tune main benchmark | No | reported in §4.11 and `eval/public_transfer/README.md` |
| Reported outcome | Citation precision 100%, ungrounded rate 0%, answer rate 91.67%, recall@5 52.1% (vs 85% on synthetic) | summary.json |

## Adversarial Probe (Appendix B.12)

| Fact | Value | Source |
|------|-------|--------|
| Query bank | 15 queries (5 attack types × 3 queries) | `eval/adversarial/adversarial_queries.csv` |
| Extractive arm | 15/15 safe, 0 fabricated citations, 0 unsupported answers | `eval/adversarial/adversarial_summary.csv` |
| Generative arm | `n/a` — OpenAI quota error (HTTP 429) on all 15 queries; preserved rather than estimated | `eval/adversarial/adversarial_results_generative.csv` |
| Scope | Small probe, not a security certification | `docs/evidence/verification/adversarial_test_summary.md` |

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
| Final B2/B3 generative runs | `backend_requested=dense`, `backend_used=bm25` (documented BM25 fallback; surfaced by `verify_artifacts.py` as `EXPECTED NOTICE`, retained on purpose) |
| `results/manifest.json` `strict` field | `false` — the offline-only evidence path verifies retained artefacts without requiring an API-enabled generative re-run; missing online-generative artefacts are preserved explicitly rather than silently filled |

## Test Suite

| Fact | Value | Source |
|------|-------|--------|
| Total test files | 39 | `tests/` directory |
| Total test cases collected | 196 | `pytest --collect-only -q` |
| Run under documented evaluator command | 194 | `pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py` |
| Passing | 193 | as above |
| Conditionally skipped | 1 | FAISS-dependent test (skipped when ML extras are absent) |

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

- No claim of multi-model evaluation (only OpenAI tested).
- No claim of real-world corpus testing (synthetic primary corpus acknowledged; Public Guidance Transfer Stress Test is a small extractive-only probe, not a full transfer evaluation).
- No claim of deployment-readiness, production-readiness, or user-study validation.
- No claim of domain-expert reviewer evaluation (CS peers only).
- No claim of formal Faculty ethics approval (the peer-review check is low-risk and judged below the threshold; supervisor was kept informed of design and timing only).
- No claim of "publishable" status. The publication route is discussed honestly in §5.3 as future work that would require larger external corpus, domain-expert annotation, and a blinded user study.

## Known Limitations (cross-reference §5.2 and Table 4.13)

- L1: synthetic primary corpus.
- L2: small public-transfer set (8 docs, 249 paragraphs, 20 queries) and Extractive Mode only.
- L3: small reviewer sample (n = 6 CS peers), author-facilitated.
- L4: BM25 fallback for the final generative runs (Recall@5 73.9% vs ≈85% dev-phase dense).
- L5: generative adversarial arm `n/a` (OpenAI quota).
- L6: Jaccard token-overlap verification cannot detect paraphrase-level support.
