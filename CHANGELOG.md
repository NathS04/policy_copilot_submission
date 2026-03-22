# Changelog

All notable changes to this project are documented in this file.
This changelog was compiled retrospectively to summarise the development
history of Policy Copilot across its major phases.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.7.0] — 2026-02-22 — Hardening & Submission Preparation

### Added
- Production-grade Streamlit workbench with 5 modes: Ask, Audit Trace,
  Critic Lens, Experiment Explorer, Reviewer
- Centralised design system (`theme.py`) and reusable UI components
- Evaluator verification guide (`INSTRUCTIONS_FOR_EVALUATOR.md`)
- Reproducibility checklist and requirements traceability matrix
- Project truth registry for canonical counts and definitions
- Research pack: literature matrix, comparator matrix, taxonomy of related
  work, gap statement, citation chains, search strategy, report mapping
- Sprint log and meeting records
- Claim-to-evidence map linking report assertions to code/artefacts
- Artefact integrity verifier (`scripts/verify_artifacts.py`)
- Smoke install script (`scripts/smoke_install.sh`)
- 38 test modules covering all major subsystems

### Changed
- Refactored UI into modular architecture: `theme.py`, `components.py`,
  `renderers.py`, `state.py`
- Improved provenance tracking: `backend_requested` vs `backend_used`
- Cleaned stale run artefacts from `results/runs/`
- Removed unused imports across codebase (ruff compliance)

### Fixed
- Forward-reference errors in `streamlit_app.py`
- Nested f-string quote escaping in `renderers.py`
- `build_index.py` exit code when ML deps are absent

## [0.6.0] — 2026-02-08 — Critic Mode & Reviewer

### Added
- Critic agent with L1–L6 heuristic and LLM-based detection
  (normative language, framing imbalance, unsupported claims, internal
  contradictions, false dilemma, slippery slope)
- Critic evaluation harness (`scripts/run_critic_eval.py`)
- Critic dataset builder (`scripts/make_critic_dataset.py`)
- Reviewer service with rubric-based human scoring
- Human evaluation pack export/import tooling
- Audit report service (JSON + HTML export)
- Run inspector for browsing past evaluation runs

### Changed
- Promoted service layer into dedicated `service/` package
  (orchestrator, audit reports, reviewer, run inspector)

## [0.5.0] — 2026-01-19 — Evaluation Harness & Golden Set

### Added
- Golden set: 63 queries (36 answerable, 17 unanswerable, 10 contradiction)
- Dev/test split with stratified categories
- Golden set validation script
- Labelling assistant (`scripts/assist_label_gold.py`)
- Figure and table generation (`eval/analysis/make_figures.py`)
- Run configuration system (`configs/run_config.json`)
- Offline and online reproduction scripts

### Changed
- Standardised output structure: `results/runs/<run_name>/`
- Evaluation metrics: answer rate, abstention accuracy, ungrounded rate,
  citation precision

## [0.4.0] — 2025-12-22 — Reliability Layer (B3)

### Added
- Cross-encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Confidence-gated abstention with configurable threshold
- Per-claim citation verification (Jaccard-based support check)
- Contradiction detection (negation pairs, numeric mismatches)
- Claim splitting heuristic
- B3 full-system baseline with ablation support
  (`--no_rerank`, `--no_verify`, `--no_contradictions`)
- Latency breakdown tracking per pipeline stage

### Changed
- Retrieval and reranking scores normalised to [0, 1] (higher = better)

## [0.3.0] — 2025-11-28 — Dense Retrieval & Hybrid Search

### Added
- FAISS vector index wrapper
- SentenceTransformers embedding generation
- Dense retrieval pipeline
- Hybrid retrieval with reciprocal-rank fusion (BM25 + dense)
- Index build script (`scripts/build_index.py`)

### Changed
- Retriever interface unified across BM25, dense, and hybrid backends

## [0.2.0] — 2025-10-31 — Ingestion & BM25 Retrieval

### Added
- PDF extraction with `pypdf` / `pdfplumber`
- Text chunking with configurable window and overlap
- Paragraph ID assignment (deterministic, content-based)
- BM25 retrieval with `rank-bm25`
- Corpus ingestion CLI (`scripts/ingest_corpus.py`)
- Naive RAG baseline (B2): retrieve top-5, send to LLM
- Prompt-only baseline (B1): no retrieval
- Query CLI (`scripts/query_cli.py`)

### Changed
- Config management via Pydantic settings

## [0.1.0] — 2025-09-29 — Project Scaffold

### Added
- Package structure with `src/` layout and `pyproject.toml`
- Pydantic-based configuration management
- Logging utilities
- Basic project config and requirements
- Initial test scaffolding
