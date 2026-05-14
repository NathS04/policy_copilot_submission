# Golden-Set Label Audit

This audit was produced by `scripts/audit_golden_set_labels.py` to flag possible mislabels in the original golden set (`eval/golden_set/golden_set.csv`). No LLM calls were used — the audit relies on stopword-stripped token overlap (Jaccard) between each query and every corpus paragraph.

- Total queries audited: **63**
- Queries flagged for review: **2**
- Queries relabelled in `golden_set_v2_corrected.csv`: **4**

## Methodology

1. Tokenise each query and each paragraph with case-folding and English stopword removal.
2. For each query, score every paragraph by Jaccard token overlap.
3. Flag any *unanswerable* query whose top candidate scores ≥ 0.1, any *answerable* query missing gold IDs, and any *contradiction* query with fewer than two candidate paragraphs above 0.05.
4. Read the flagged paragraphs by hand; relabel only if the corpus genuinely answers the question.

## Relabel decisions

| Query | Old | New | Gold added | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| q_014 | unanswerable | answerable | `hr_procedures_manual::p0009::i0000::ceb3a6266920` | HR Procedures Manual paragraph p0009::i0000 states 'The standard notice period is: 1 month for employees below senior management, ...'. |
| q_016 | unanswerable | answerable | `hr_procedures_manual::p0008::i0000::559a594dc2ac,hr_procedures_manual::p0008::i0001::cedb99dfaf25,hr_procedures_manual::p0008::i0002::01ccd9d70161` | HR Procedures Manual §7 'Grievance Procedure' (paragraphs p0008::i0000 through p0008::i0002) sets out the formal procedure, hearing, appeal and non-retaliation policy. |
| q_062 | unanswerable | answerable | `hr_procedures_manual::p0006::i0002::8c5195f8b5ea` | HR Procedures Manual paragraph p0006::i0002 explicitly states: 'Requests for unpaid leave, sabbaticals, or career breaks must be submitted to HR at least 3 months in advance. Approval is at the discretion of the department head and HR Director.' — the company does offer sabbatical leave, by application. |
| q_004 | unanswerable | answerable | `internal_policy_handbook_v2::p0014::i0000::22101d8d9bb7,internal_policy_handbook_v2::p0014::i0001::57e8f6f4cafc,internal_policy_handbook_v2::p0014::i0002::051345293182,internal_policy_handbook_v2::p0014::i0003::c79e6cb648ff` | Internal Policy Handbook §13 'Bring Your Own Device (BYOD) Policy' (paragraphs p0014::i0000-i0003) explicitly states 'Employees may use personal devices (smartphones, tablets, laptops) for work purposes subject to the conditions in this section' and sets out the BYOD enrolment, MDM, secure-container, and reporting requirements. |

## All flagged queries

Listed verbatim from `results/tables/golden_set_label_audit.csv`. Decisions are inline.

### q_004 — Are employees allowed to use personal devices for work?

- **Original**: `unanswerable` / gold: `(none)`
- **Top candidate**: `internal_policy_handbook_v2::p0009::i0000::40d044dc00be` (score 0.1379, terms: devices,personal,use,work)
- **Flags**: unanswerable_but_corpus_hit:score=0.138
- **Decision**: relabel to `answerable` with gold `internal_policy_handbook_v2::p0014::i0000::22101d8d9bb7,internal_policy_handbook_v2::p0014::i0001::57e8f6f4cafc,internal_policy_handbook_v2::p0014::i0002::051345293182,internal_policy_handbook_v2::p0014::i0003::c79e6cb648ff`. Internal Policy Handbook §13 'Bring Your Own Device (BYOD) Policy' (paragraphs p0014::i0000-i0003) explicitly states 'Employees may use personal devices (smartphones, tablets, laptops) for work purposes subject to the conditions in this section' and sets out the BYOD enrolment, MDM, secure-container, and reporting requirements.

### q_006 — Is data encryption required for public non-sensitive information?

- **Original**: `unanswerable` / gold: `(none)`
- **Top candidate**: `internal_policy_handbook_v2::p0015::i0001::d2998ba49253` (score 0.1, terms: data,encryption,public,sensitive)
- **Flags**: unanswerable_but_corpus_hit:score=0.100
- **Decision**: keep as-is. 

