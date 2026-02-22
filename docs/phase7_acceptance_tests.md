# Phase 7 Acceptance Tests

## Automated Tests

All tests can be run with `pytest tests/` from the project root.

### New test files

| Test file                     | What it covers                            | Pass criteria            |
|-------------------------------|-------------------------------------------|--------------------------|
| `test_chat_orchestrator.py`   | Pipeline flow, abstention, errors, config | All assertions pass      |
| `test_audit_report_export.py` | JSON/HTML/Markdown export, round-trip     | All required fields exist|
| `test_hybrid_retrieval.py`    | RRF formula, alpha, fallback, metadata    | Deterministic scores     |
| `test_run_inspector.py`       | Listing, loading, comparing runs          | Correct deltas/records   |
| `test_ui_state.py`            | Session state init, views, messages       | All state transitions    |

### Pre-existing tests

All 27 existing tests must continue to pass without modification.

## Manual Acceptance Criteria

### Ask View

- [ ] Chat input accepts questions and displays responses
- [ ] Inline citation pills appear after answers
- [ ] Confidence badge shows HIGH/MODERATE/LOW
- [ ] Abstention banner appears for unanswerable questions
- [ ] Contradiction warnings appear when contradictions detected
- [ ] "View Audit Trace", "Run Critic", "Export Report" buttons work

### Audit Trace View

- [ ] Can select previous queries from dropdown
- [ ] Claim-by-claim table shows supported/unsupported status
- [ ] Evidence rail shows paragraph text with scores
- [ ] Contradiction section shows side-by-side passages
- [ ] Metadata panel shows provider, model, backend, latency
- [ ] JSON download produces valid JSON
- [ ] HTML download produces self-contained HTML page

### Critic Lens View

- [ ] Text area accepts pasted text for analysis
- [ ] L1-L6 flags display with triggers and rationale
- [ ] Evidence tab analyses paragraphs from last query
- [ ] Label filter works when multiple labels present
- [ ] Export produces valid JSON

### Experiment Explorer View

- [ ] Lists all runs from results/runs/
- [ ] Run detail shows summary metrics, config, and per-query records
- [ ] Comparison shows metric deltas between two runs

### Hybrid Retrieval

- [ ] When both dense and BM25 backends are available, fusion method is "rrf"
- [ ] When only one backend is available, falls back gracefully
- [ ] Each result records dense_rank, sparse_rank, fused_score

### Architecture

- [ ] No business logic in Streamlit files
- [ ] All pipeline logic in service/chat_orchestrator.py
- [ ] All structured outputs use Pydantic models from service/schemas.py

## What is NOT tested

- LLM-dependent behaviour (requires API key; tested in existing integration tests)
- Visual rendering (Streamlit components; manual inspection required)
- Performance under load (out of scope for dissertation)
