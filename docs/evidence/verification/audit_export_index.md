# Audit Export Evidence: Index

Three representative audit-export examples extracted from the
B3-Generative final run
(`results/runs/b3_generative_bm25_fallback_final/outputs.jsonl`).
Every value in each example is a verbatim copy from the run's
outputs file - nothing is summarised or fabricated.

| Case | File | query_id | status |
| :--- | :--- | :--- | :--- |
| Answerable | `audit_export_answerable.md` | `q_018` | Answered |
| Unanswerable / Abstained | `audit_export_unanswerable.md` | `q_004` | Abstained |
| Contradiction | `audit_export_contradiction.md` | `q_057` | Answered |

## What each example demonstrates

- **Answerable:** clean grounded-answer audit trail. Every
  citation maps to a real paragraph; claim verification
  reports `support_rate = 1.0`; no contradictions; the
  reviewer can verify the answer against the cited paragraphs
  alone.
- **Unanswerable / Abstained:** clean refusal audit trail.
  The system declined with `INSUFFICIENT_EVIDENCE`; the
  notes field records whether the abstention was triggered
  by `ABSTAINED_LOW_SUPPORT_RATE` (post-LLM verification gate)
  or `ABSTAINED_LOW_CONFIDENCE` (pre-LLM rerank gate).
- **Contradiction:** contradiction-flag audit trail. The
  contradictions list preserves the structured tension the
  system surfaced; the candidate evidence is preserved so a
  reviewer can adjudicate.

## Reproduction

These three files are regenerated deterministically by
`python scripts/build_audit_exports.py`; the script reads
the existing `outputs.jsonl` and writes the three markdown
files plus this index. No new system runs are performed.

Generated: 2026-05-06T00:28:24.129868+00:00
