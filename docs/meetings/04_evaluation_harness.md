# Meeting 04 — Evaluation Harness and Critic Mode

**Date:** Early January 2025 (reconstructed summary)
**Attendees:** Student, Supervisor

## Agenda
1. Review evaluation harness design
2. Discuss critic mode implementation
3. Plan human evaluation approach

## Progress Summary
- Full B3 pipeline operational with ablation support
- Evaluation harness (`run_eval.py`) producing structured outputs (JSONL, CSV, summary JSON)
- Implemented critic mode with L1-L6 heuristic detection; LLM-based detection as optional tier
- Created critic evaluation dataset with neutral and manipulated variants
- Discussed human evaluation: agreed single-rater self-evaluation is realistic given project constraints, with inter-rater agreement noted as future work

## Agreed Actions
- [ ] Finalise the golden set validation script
- [ ] Run all three baselines (B1, B2, B3) on the full golden set
- [ ] Run ablation experiments
- [ ] Conduct human evaluation on a 20-query sample
- [ ] Design the figure/table generation pipeline for the report

---
*Note: This summary was reconstructed from project records and commit history to document the supervision process.*
