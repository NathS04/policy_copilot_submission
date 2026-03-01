# Meeting 02 — Corpus Design and Retrieval Strategy

**Date:** Late October 2024 (reconstructed summary)
**Attendees:** Student, Supervisor

## Agenda
1. Review corpus design decisions
2. Discuss retrieval backend choices
3. Review golden set design

## Progress Summary
- Completed PDF ingestion pipeline with paragraph-level chunking and stable IDs
- Built BM25 (sparse) retriever; FAISS (dense) retriever deferred to after baseline evaluation
- Designed the golden set structure: answerable, unanswerable, and contradiction categories
- Discussed the trade-off between synthetic and real policy corpora; agreed synthetic is justified for controlled evaluation

## Agreed Actions
- [ ] Complete the golden set with at least 60 queries across all three categories
- [ ] Implement B1 (prompt-only) and B2 (naive RAG) baselines
- [ ] Run initial baseline evaluation to establish the performance floor
- [ ] Begin implementing the cross-encoder reranker

---
*Note: This summary was reconstructed from project records and commit history to document the supervision process.*
