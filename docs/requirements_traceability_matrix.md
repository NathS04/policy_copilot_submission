# Requirements Traceability Matrix

Maps each functional and non-functional requirement to its implementing source files, tests, and evaluation evidence.

## Functional Requirements

| Req | Description | Source Files | Tests | Evaluation Evidence |
|-----|-------------|-------------|-------|---------------------|
| FR1 | Evidence-grounded answers with paragraph-level citations | `generate/answerer.py`, `generate/prompts.py`, `generate/schema.py` | `test_generation_schema.py`, `test_extractive_fallback.py`, `test_extractive_fallback_inline_citations.py` | B2/B3 runs: `citation_precision`, `citation_recall` in `summary.json` |
| FR2 | Abstention on insufficient evidence | `verify/abstain.py`, `service/chat_orchestrator.py` | `test_abstain.py`, `test_b3_fallback_relevance_gate.py`, `test_b3_fallback_relevance_pass.py` | B3 run: `abstention_accuracy=0.9412` in `summary.json` |
| FR3 | Claim-evidence mapping and verification | `verify/claim_split.py`, `verify/citation_check.py` | `test_claim_verification.py`, `test_claim_split_skips_numbering.py` | B3 run: `support_rate_mean`, `ungrounded_rate=0` in `summary.json` |
| FR4 | Contradiction detection and surfacing | `verify/contradictions.py`, `verify/llm_judges.py` | `test_contradictions.py` | B3 run: `contradiction_recall`, `contradiction_precision` in `summary.json` |
| FR5 | Audit report export (JSON, HTML) | `service/audit_report_service.py`, `service/schemas.py` | `test_audit_report_export.py` | Export functionality in Audit Trace view |
| FR6 | Critic mode (L1-L6 policy language analysis) | `critic/critic_agent.py`, `critic/labels.py` | `test_critic.py` | Critic eval: 93.7% macro precision (report Section 4.6) |

## Non-Functional Requirements

| Req | Description | Source Files | Tests | Evaluation Evidence |
|-----|-------------|-------------|-------|---------------------|
| NFR1 | Usability — modern chat interface | `ui/streamlit_app.py`, `ui/components.py`, `ui/state.py` | `test_ui_state.py` | UI screenshots in `docs/report/figures/` |
| NFR2 | Transparency — visible confidence and evidence | `ui/components.py` (confidence badge, evidence rail, citation pills) | `test_chat_orchestrator.py` | Audit Trace view, inline citation pills |
| NFR3 | Reproducibility — config snapshots, run browsing | `service/run_inspector.py`, `scripts/reproduce_offline.py`, `scripts/reproduce_online.py` | `test_run_inspector.py`, `test_verify_artifacts_smoke.py` | `results/runs/` artifacts, `results/manifest.json` |
| NFR4 | Auditability — structured export of pipeline steps | `service/schemas.py`, `service/audit_report_service.py` | `test_audit_report_export.py` | JSON/HTML export with full pipeline metadata |

## Baseline Traceability

| Baseline | Description | Implementation | Evaluation Run |
|----------|-------------|----------------|----------------|
| B1 | Prompt-only LLM (no retrieval) | `generate/answerer.py::generate_b1()` | `results/runs/b1_generative_final/` |
| B2 | Naive RAG (top-5, no reranking/abstention) | `generate/answerer.py::generate_b2()` | `results/runs/b2_generative_bm25_fallback_final/` |
| B3 | Full system (rerank + abstain + verify + contradictions) | `service/chat_orchestrator.py`, `scripts/run_eval.py::_run_b3_query()` | `results/runs/b3_generative_bm25_fallback_final/` |
