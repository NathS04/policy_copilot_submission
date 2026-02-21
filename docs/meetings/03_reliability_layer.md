# Meeting 03 — Reliability Layer Design

**Date:** Mid-November 2024 (reconstructed summary)
**Attendees:** Student, Supervisor

## Agenda
1. Review B3 reliability pipeline design
2. Discuss abstention threshold calibration
3. Plan contradiction detection approach

## Progress Summary
- B1 and B2 baselines running and producing results
- Designed the B3 reliability pipeline: retrieve → rerank → confidence gate → generate → verify → contradictions
- Implemented per-claim citation verification using Jaccard token overlap
- Discussed abstention: agreed on a confidence-gated approach using max reranker score
- Reviewed the claim-splitting approach for sentence-level verification

## Agreed Actions
- [ ] Implement contradiction detection (antonym/negation pairs + numeric mismatch heuristics)
- [ ] Calibrate the abstention threshold on the dev split (not the test split)
- [ ] Add ablation flags (--no_rerank, --no_verify, --no_contradictions) for component analysis
- [ ] Begin the critic mode design (L1-L6 policy language labels)

---
*Note: This summary was reconstructed from project records and commit history to document the supervision process.*
