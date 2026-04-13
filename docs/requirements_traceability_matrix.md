# Requirements Traceability Matrix

Maps each functional and non-functional requirement to its implementing source files, tests, and evaluation evidence.

## Functional Requirements

| Req | Description | Source Files | Tests | Evaluation Evidence |
|-----|-------------|-------------|-------|---------------------|
| FR1 | Evidence-grounded answers with paragraph-level citations | `generate/answerer.py`, `generate/prompts.py`, `generate/schema.py` | `test_generation_schema.py`, `test_extractive_fallback.py`, `test_extractive_fallback_inline_citations.py` | B2/B3 runs: `citation_precision`, `citation_recall` in `summary.json` |
| FR2 | Abstention on insufficient evidence | `verify/abstain.py`, `service/chat_orchestrator.py` | `test_abstain.py`, `test_b3_fallback_relevance_gate.py`, `test_b3_fallback_relevance_pass.py` | B3 run: `abstention_accuracy=0.9412` in `summary.json` |
| FR3 | Citation verification (per-claim support checking) | `verify/claim_split.py`, `verify/citation_check.py` | `test_claim_verification.py`, `test_claim_split_skips_numbering.py` | B3 run: `support_rate_mean`, `ungrounded_rate=0` in `summary.json` |
| FR4 | Extractive fallback (LLM-free operation) | `generate/answerer.py` (`make_llm_disabled`), `service/chat_orchestrator.py` | `test_extractive_fallback.py`, `test_b2_extractive_integration.py` | B3-Extractive: 100% citation precision by construction |
| FR5 | Contradiction detection and surfacing | `verify/contradictions.py`, `verify/llm_judges.py` | `test_contradictions.py` | B3 run: `contradiction_recall`, `contradiction_precision` in `summary.json` |
| FR6 | Critic mode (L1-L6 policy language analysis) | `critic/critic_agent.py`, `critic/labels.py` | `test_critic.py` | Critic eval: 93.7% macro precision (report Section 4.7) |

## Non-Functional Requirements

| Req | Description | Source Files | Tests | Evaluation Evidence |
|-----|-------------|-------------|-------|---------------------|
| NFR1 | Latency — P95 end-to-end < 10s | All pipeline modules | `test_chat_orchestrator.py` | Table 4.7a: B3 P95 = 4.9s |
| NFR2 | Reproducibility — all results scriptable and deterministic | `scripts/run_eval.py`, `scripts/reproduce_offline.py`, `scripts/reproduce_online.py` | `test_run_inspector.py`, `test_verify_artifacts_smoke.py` | `results/runs/` artifacts, `results/manifest.json` |
| NFR3 | Modularity — components toggleable independently | `service/chat_orchestrator.py`, `scripts/run_eval.py` (ablation flags) | `test_b3_fallback_relevance_gate.py` | Ablation study: `--no_rerank`, `--no_verify`, `--no_contradictions`; `results/tables/ablation_comparison.csv` |
| NFR4 | Auditability — provenance, traceability, evidence integrity | `service/schemas.py`, `service/audit_report_service.py`, `scripts/verify_artifacts.py` | `test_audit_report_export.py`, `test_verify_artifacts_smoke.py` | Risk audit table: `docs/risk_audit_table.md`; Auditability rubric: `eval/rubrics/auditability_rubric.md`; Failure taxonomy: `results/tables/failure_taxonomy.csv` |

## Baseline Traceability

| Baseline | Description | Implementation | Evaluation Run |
|----------|-------------|----------------|----------------|
| B1 | Prompt-only LLM (no retrieval) | `generate/answerer.py::generate_b1()` | `results/runs/b1_generative_final/` |
| B2 | Naive RAG (top-5, no reranking/abstention) | `generate/answerer.py::generate_b2()` | `results/runs/b2_generative_bm25_fallback_final/` |
| B3 | Full system (rerank + abstain + verify + contradictions) | `service/chat_orchestrator.py`, `scripts/run_eval.py::_run_b3_query()` | `results/runs/b3_generative_bm25_fallback_final/` |
