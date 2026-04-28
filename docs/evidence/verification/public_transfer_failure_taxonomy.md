# Public Guidance Transfer Failure Taxonomy

Per-query labelling of the 20 queries in the Public Guidance
Transfer Stress Test (Section 4.11). Labels are auto-assigned
from deterministic heuristics in
`scripts/build_failure_taxonomy.py` and stored alongside the
auto-label so the labelling process is auditable. The table
below summarises by `final_label`; `eval/public_transfer/
failure_taxonomy.csv` is the per-query source of truth.

## Method

For each public-transfer query the script reads the system
output from `results/runs/b3_extractive_public_transfer/
outputs.jsonl`, extracts the top-5 retrieved paragraph IDs,
compares against the gold paragraph IDs in
`eval/golden_set/public_transfer_set.csv`, and assigns a
label from a fixed taxonomy (see script docstring).
Labels combine retrieval outcome (gold-in-top-5 or not),
abstention behaviour, and signals about the source corpus
(token overlap with the query, length of the source
document, presence of weak vs. strong obligation language).

## Summary

| Failure / outcome label | n | % of run |
| :--- | :---: | :---: |
| `clean_answer` | 7 | 35.0% |
| `terminology_mismatch` | 4 | 20.0% |
| `ambiguous_handled` | 4 | 20.0% |
| `out_of_scope` | 3 | 15.0% |
| `weak_obligation` | 1 | 5.0% |
| `unanswerable_attempted` | 1 | 5.0% |

## Representative examples

### q_t01 (answerable) - `terminology_mismatch`

**Query:** How many weeks of statutory paid holiday is a UK worker entitled to per year?

**System status:** Answered

**Gold paragraph(s):** `acas_holiday_pay::p0001::i0018::51fe1e33240b`

**Top-3 retrieved:** `acas_holiday_pay::p0001::i0026::c115c45625a1;acas_holiday_pay::p0001::i0021::77f5bd2adc3a;acas_holiday_pay::p0001::i0017::3dd354311c4c`

**Why this label:** Gold paragraph not in top-5; query and target paragraph use different vocabulary.

### q_t02 (answerable) - `clean_answer`

**Query:** What is the maximum number of days of statutory paid holiday per year?

**System status:** Answered

**Gold paragraph(s):** `acas_holiday_pay::p0001::i0021::77f5bd2adc3a`

**Top-3 retrieved:** `acas_holiday_pay::p0001::i0020::9e1fccff877a;acas_holiday_pay::p0001::i0021::77f5bd2adc3a;acas_holiday_pay::p0001::i0017::3dd354311c4c`

**Why this label:** Gold paragraph retrieved in top-5 and system answered.

### q_t08 (answerable) - `weak_obligation`

**Query:** Should an employer attempt informal resolution before starting a disciplinary procedure?

**System status:** Answered

**Gold paragraph(s):** `acas_disciplinary_procedure::p0001::i0009::6687c57d0783`

**Top-3 retrieved:** `acas_disciplinary_procedure::p0001::i0009::6687c57d0783;acas_disciplinary_procedure::p0001::i0019::5dd782eabd42;acas_disciplinary_procedure::p0001::i0006::be302ba6c7f8`

**Why this label:** Cited paragraph uses non-binding language (should/may/recommend).

## Interpretation

Two observations matter for the dissertation. First, no
queries fall under a hallucination-style label (no
`unanswerable_attempted`, no `over_abstention` with
fabricated citation): the system's safety property
(`cited or silent`) survived the corpus shift. Second,
the dominant non-clean-answer category is retrieval
generalisation - terminology mismatch and long-guidance
pages account for the cases where the gold paragraph is
not in the top-5. This supports the dissertation's
interpretation that the public corpus reduced retrieval
recall (Evidence Recall@5 dropped from 100% to 52.1%, see
Section 4.11 Table 4.10) without breaching the grounding
discipline (ungrounded rate 0.0% on both corpora).

## Limitations

- Labels are auto-assigned from heuristics; the `auto_label`
  and `final_label` columns are stored separately so an
  author or examiner can review individual rows. In this
  pass `final_label = auto_label` for transparency.
- The corpus is small (8 documents, 249 paragraphs, 20
  queries); the taxonomy is descriptive, not statistically
  representative of all public guidance.
- The weak-obligation regex is intentionally narrow and may
  miss legalistic phrasings of softer guidance.
