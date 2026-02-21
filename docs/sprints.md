# Sprint / Milestone Log

This document maps the project milestones from the outline specification to the actual development phases and their key deliverables.

## Milestone Map

| Sprint | Period | Outline Spec Milestone | Key Deliverables | Status |
|--------|--------|------------------------|------------------|--------|
| S1 | Oct 2024 | M1: Corpus + IDs | PDF ingestion pipeline, paragraph-level chunking, stable paragraph IDs, corpus manifest | Complete |
| S2 | Oct-Nov 2024 | M2: Naive RAG + early golden set | BM25 retriever, B1 and B2 baselines, golden set v1 (63 queries), evaluation harness skeleton | Complete |
| S3 | Nov-Dec 2024 | M3: Reranking + citations + abstention | Cross-encoder reranker, confidence-gated abstention, per-claim citation verification, claim splitting | Complete |
| S4 | Dec 2024-Jan 2025 | M4: Contradiction + critic mode | Contradiction detection (heuristic + optional LLM), critic agent (L1-L6), critic evaluation dataset | Complete |
| S5 | Jan-Feb 2025 | M5: Eval harness + ablations + error analysis | Full B1/B2/B3 evaluation, ablation experiments (no-rerank, no-verify, no-contradictions), figure generation, human evaluation (20 queries) | Complete |
| S6 | Feb-Mar 2025 | M6: Report + figures/tables/appendices | Service layer extraction, multi-mode UI (Ask, Audit Trace, Critic Lens, Experiment Explorer), hybrid retrieval (RRF), audit export, package hardening, report drafting | Complete |

## Key Technical Decisions by Sprint

### S1 — Corpus and Ingestion
- Chose paragraph-level chunking over sentence-level: paragraphs preserve enough context for policy interpretation while remaining attributable
- Designed stable paragraph IDs (`doc::page::para_idx::hash`) for reproducible citation

### S2 — Baselines and Evaluation
- Chose BM25 as the primary offline retrieval backend for reproducibility without GPU
- Designed three-tier baseline ladder (B1 → B2 → B3) to isolate each reliability component's contribution
- Split golden set into dev (18 queries) and test (45 queries) subsets

### S3 — Reliability Layer
- Chose Jaccard token overlap (threshold 0.10) for Tier-1 claim verification: deterministic, interpretable, no external model dependency
- Chose max reranker score as the abstention signal: directly measures evidence quality
- Calibrated abstention threshold on dev split only to avoid data leakage

### S4 — Critic Mode
- Designed L1-L6 label taxonomy covering normative language, framing, unsupported claims, contradictions, false dilemma, and slippery slope
- Chose regex/keyword heuristics as Tier-1 with optional LLM as Tier-2: ensures reproducibility and transparency

### S5 — Evaluation
- Conducted ablation experiments to isolate reranking, verification, and contradiction detection contributions
- Discovered reranking is more impactful than verification (counter to initial hypothesis)
- Adopted bootstrapped confidence intervals (1000 samples) for statistical rigour

### S6 — Packaging and UI
- Extracted B3 pipeline from `run_eval.py` into `ChatOrchestrator` service class for testability
- Implemented Reciprocal Rank Fusion (RRF) for hybrid retrieval with documented alpha/k parameters
- Built four-view Streamlit interface with clean UI/service/core separation
