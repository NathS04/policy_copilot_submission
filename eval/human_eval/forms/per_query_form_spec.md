# Per-Query Independent Reviewer Evaluation: Form Spec

This file is the master copy of the per-query reviewer form. Drop the
text below into a Google Form, Microsoft Forms, or Qualtrics; configure
each section as instructed; share the link with reviewers; export the
responses as CSV; and save them as
`eval/human_eval/per_query_raw.csv` for ingestion by
`scripts/compute_human_eval.py`.

This is the second round of the Independent Reviewer Evaluation. The
first round (P1-P6, April 2026) recorded only per-participant
aggregate Likert scores; this round records **per-(participant, query)
ratings** so that inter-rater agreement (Krippendorff's alpha for
ordinal Likert data) can be computed honestly.

## Form configuration

- Set "Collect email addresses" = **Off**.
- Set "Limit to 1 response per person" = **Off** (anonymous).
- Set "Allow respondents to edit after submit" = **Off**.
- Linked Google Sheet: rename the auto-created sheet to
  `per_query_responses`. Export to CSV when collection closes.

## Question 0 - Anonymous participant tag

Display text:

> Please choose an anonymous participant tag. Use the next free letter:
> Q1 (first respondent), Q2, Q3, ... You will not be asked for your
> name, email, or any other personal information. The tag is used only
> to compute inter-rater agreement.

Question type: short answer (regex validation: `^Q\d+$`).

## Question 1 - Role

Display text:

> Which best describes your current role?

Question type: multiple choice. Options:

- BSc Computer Science (Final Year)
- MSc Computer Science
- BSc Computer Science (other year)
- Other (please skip the form)

## Question 2 - Consent

Display text (mirrors `eval/human_eval/consent_text.md`):

> By continuing, you confirm that:
>
> 1. You have read the participant information at
>    `docs/evidence/human_eval/participant_info.md`.
> 2. You consent to your anonymised Likert ratings (1-5) and any
>    optional one-line comments being used in the dissertation
>    Section 4.10 and Appendix B.10.
> 3. You understand you may withdraw before final submission by
>    contacting the author. After submission your data is anonymised
>    such that withdrawal is no longer technically possible.
> 4. You understand no name, email, or quoted text identifying you
>    will appear in the report.

Question type: multiple choice. Options:

- Yes, I consent and would like to continue.
- No, I do not consent (the form will end).

Add a branch: if "No", end form.

## Sections 3-22 - Per-query rating blocks

There are exactly **20 sections**, one per query. The query identifiers
are `Q01` through `Q20` and the query text is taken verbatim from the
B3-Generative test run sample documented in
`eval/human_eval/rubric.md`.

Each section follows the same template. Replace `{{QUERY_TEXT}}`,
`{{ANSWER_OR_REFUSAL}}`, `{{CITED_PARAGRAPHS}}`, `{{STATUS_BADGE}}`,
and `{{QUERY_TYPE}}` per query.

> **Query {{QUERY_ID}} ({{QUERY_TYPE}})**
>
> *Question:* {{QUERY_TEXT}}
>
> *System answer:* {{ANSWER_OR_REFUSAL}}
>
> *Cited paragraphs:* {{CITED_PARAGRAPHS}}
>
> *System status:* {{STATUS_BADGE}}

Then five 1-5 Likert questions (radio, required):

1. **Correctness:** Does the answer (or refusal) match what the cited
   evidence says? **(1 = poor, 5 = excellent)**
2. **Groundedness:** Is every claim in the answer visibly supported by
   the cited paragraphs? **(1 = poor, 5 = excellent)**
3. **Citation Usefulness:** Do the citations help you verify the
   answer yourself? **(1 = poor, 5 = excellent)**
4. **Usefulness:** Would the output help a real user answer the
   underlying policy question? **(1 = poor, 5 = excellent)**
5. **Trust Calibration:** Does the system express appropriate
   uncertainty / refusal when evidence is weak?
   **(1 = poor, 5 = excellent)**

Plus one optional question:

6. **One-line comment** (optional): What is the strongest or weakest
   thing about this output? *Free text, single sentence.*

## Per-query content (paste into the form, one section each)

| Q  | type           | mode    | text source                                                                |
| -- | -------------- | ------- | -------------------------------------------------------------------------- |
| Q01 | answerable    | B3-Gen | direct factual; clean citation                                             |
| Q02 | answerable    | B3-Gen | direct factual; clean citation                                             |
| Q03 | answerable    | B3-Gen | direct factual; multi-citation                                             |
| Q04 | answerable    | B3-Gen | direct factual; clean citation                                             |
| Q05 | answerable    | B3-Gen | counts/numerical answer                                                    |
| Q06 | answerable    | B3-Gen | direct factual; longer answer                                              |
| Q07 | answerable    | B3-Gen | conditional answer with hedges                                             |
| Q08 | answerable    | B3-Gen | direct yes/no                                                              |
| Q09 | over-abstain  | B3-Gen | answerable case the system refused (reviewer should grade Trust low)       |
| Q10 | over-abstain  | B3-Gen | answerable case the system refused                                         |
| Q11 | over-abstain  | B3-Gen | answerable case the system refused                                         |
| Q12 | over-abstain  | B3-Gen | answerable case the system refused                                         |
| Q13 | unanswerable  | B3-Gen | clean refusal                                                              |
| Q14 | unanswerable  | B3-Gen | clean refusal                                                              |
| Q15 | unanswerable  | B3-Gen | clean refusal                                                              |
| Q16 | unanswerable  | B3-Gen | clean refusal                                                              |
| Q17 | contradiction | B3-Gen | multi-source tension surfaced                                              |
| Q18 | contradiction | B3-Gen | multi-source tension surfaced                                              |
| Q19 | contradiction | B3-Gen | multi-source tension surfaced                                              |
| Q20 | contradiction | B3-Gen | multi-source tension surfaced                                              |

The exact `{{QUERY_TEXT}}` and `{{ANSWER_OR_REFUSAL}}` strings for each
of Q01-Q20 are fetched from
`results/runs/b3_generative_bm25_fallback_final/outputs.jsonl` at
ingestion time so the form text and the report agree.

## Output schema (Google Sheet to CSV export)

The Google Sheet should look like this when exported. Each row is one
(participant, query) rating; the script tolerates either wide-form
(one column per axis per query, as Google Forms emits by default) or
long-form (one row per (participant, query)).

Long form (preferred — paste into `eval/human_eval/per_query_raw.csv`):

```csv
participant_id,role,query_id,query_type,mode,correctness,groundedness,citation_usefulness,usefulness,trust_calibration,short_comment
Q1,MSc CS,Q01,answerable,B3-Gen,5,5,4,4,5,Citations made it easy to verify
Q1,MSc CS,Q02,answerable,B3-Gen,5,5,5,4,5,
...
```

Wide form (Google Forms default — the script reshapes it
automatically):

```csv
Timestamp,Q0_id,Q1_role,Q2_consent,Q01_correctness,Q01_groundedness,Q01_citation,Q01_usefulness,Q01_trust,Q01_comment,Q02_correctness,...
2026-04-22 14:11:32,Q1,MSc CS,Yes I consent,5,5,4,4,5,Citations made it easy to verify,5,...
```

`scripts/compute_human_eval.py` accepts both formats; for long form,
column headers must match the schema exactly.

## What the ingestion script computes

1. Per-axis mean, SD, median, N - overall and per category
   (answerable / unanswerable / over-abstention / contradiction).
2. **Krippendorff's alpha (ordinal)** per axis, with bootstrap 95% CI
   over 1,000 resamples.
3. Pairwise % agreement after binning Likert scores
   {1-2 -> low, 3 -> mid, 4-5 -> high}, as a robustness check.
4. Three outputs:
   - `docs/evidence/human_eval/anonymised_scores.csv` (per-query rows)
   - `docs/evidence/human_eval/summary_stats.csv`
   - `docs/evidence/human_eval/inter_rater_agreement.md`

If fewer than 3 reviewers complete the form, agreement metrics are not
computed and `inter_rater_agreement.md` records this honestly.

## Anonymisation policy (unchanged from Round 1)

- IDs are `Q1`, `Q2`, ... assigned at form submission. No name, email,
  course code, or other personal identifier is collected.
- Free-text comments are coded into themes after the form closes; the
  raw comments stay only in the unpublished CSV. The dissertation
  shows themes only, never verbatim quotes.
- The Google Form is configured not to collect respondent email
  addresses.
