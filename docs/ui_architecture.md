# UI Architecture — Phase 7

## Three-Layer Design

```
┌─────────────────────────────────────────────────────┐
│  UI Layer (Streamlit)                               │
│  streamlit_app.py  renderers.py  components.py      │
│  state.py  theme.py                                 │
├─────────────────────────────────────────────────────┤
│  Service Layer                                      │
│  chat_orchestrator  audit_report  run_inspector     │
│  reviewer_service  schemas.py (Pydantic models)     │
├─────────────────────────────────────────────────────┤
│  Core Modules                                       │
│  retrieve/  generate/  verify/  critic/             │
│  rerank/   index/     ingest/                       │
└─────────────────────────────────────────────────────┘
```

### UI Layer (`src/policy_copilot/ui/`)

| File              | Purpose                                                |
|-------------------|--------------------------------------------------------|
| `streamlit_app.py`| Page config, sidebar, view router, service singletons  |
| `renderers.py`    | Per-mode rendering orchestrators (Ask, Audit, etc.)    |
| `components.py`   | Reusable rendering widgets (evidence cards,            |
|                   | citation pills, claim rows, critic flags, etc.)        |
| `state.py`        | Session state init and helpers                         |
| `theme.py`        | Centralised design tokens, CSS, badge/status helpers   |

### Service Layer (`src/policy_copilot/service/`)

| File                     | Purpose                                    |
|--------------------------|--------------------------------------------|
| `schemas.py`             | Pydantic models for all structured outputs |
| `chat_orchestrator.py`   | Full B3 pipeline for interactive queries   |
| `audit_report_service.py`| JSON/HTML/Markdown audit report export     |
| `run_inspector.py`       | Browse and compare evaluation runs         |
| `reviewer_service.py`    | Human rubric scoring and export            |

### Core Modules (unchanged)

Existing modules for retrieval, generation, verification, and critic analysis
are used as-is by the service layer.

## Data Flow

### Interactive Query

```
User question
  → ChatOrchestrator.process_query()
    → HybridRetriever.retrieve() or Retriever.retrieve()
    → Reranker.rerank()
    → compute_confidence() → should_abstain()
    → Answerer.generate_b3()
    → split_claims() → verify_claims() → enforce_support_policy()
    → detect_contradictions() → apply_contradiction_policy()
    → detect_heuristic() (critic)
  → QueryResult (Pydantic model)
    → stored in st.session_state
    → rendered by components.py
```

### Audit Export

```
QueryResult
  → AuditReportService.generate_report()
  → AuditReport (Pydantic model)
    → .to_json()  → JSON download
    → .to_html()  → HTML download (Jinja2 template)
    → .to_markdown() → Markdown string
```

### Experiment Explorer

```
RunInspector.list_runs()
  → reads results/runs/*/summary.json + run_config.json
  → List[RunSummary]

RunInspector.load_run(name)
  → reads outputs.jsonl → List[RunQueryRecord]
  → RunDetail

RunInspector.compare_runs(a, b)
  → metric deltas + per-query pairing
  → ComparisonResult
```

## Export Formats

| Format   | Content                                               |
|----------|-------------------------------------------------------|
| JSON     | Full QueryResult with all pipeline metadata           |
| HTML     | Self-contained audit dossier with styled tables       |
| Markdown | Lightweight text version for appendices               |

All export formats include: question, answer, claim-by-claim verification,
evidence with scores, contradictions, critic findings, confidence metrics,
config snapshot, provider/model/backend metadata, and timestamps.

## Hybrid Retrieval

The `HybridRetriever` implements Reciprocal Rank Fusion (RRF):

```
score(d) = alpha / (k + rank_dense(d)) + (1 - alpha) / (k + rank_sparse(d))
```

- `alpha = 0.5` (equal weighting, adjustable)
- `rrf_k = 60` (standard smoothing constant)
- Falls back to single-backend if one retriever is unavailable
- Records `dense_rank`, `sparse_rank`, `fused_score` per result
