# Human Evaluation

## Design

An independent reviewer evaluation was conducted between 14 and 18 April 2026 on 20 query-response pairs sampled from the B3-Generative test run. Each pair was scored on a 1-to-5 Likert scale across five dimensions: **Correctness**, **Groundedness**, **Citation Usefulness**, **Usefulness**, and **Trust Calibration**. The full rubric definition is in [`rubric.md`](rubric.md).

## Reviewers

Six volunteer reviewers from the University of Leeds School of Computer Science (three Final-Year BSc CS students and three MSc CS students), recruited outside the project supervisory chain. Reviewers are referred to only as `P1`-`P6` with a non-identifying role tag (`BSc CS` / `MSc CS`); no names, emails, or other personal data are retained.

The participant information / consent text given to each reviewer is in [`consent_text.md`](consent_text.md).

## Files

- [`independent_review_results.csv`](independent_review_results.csv) - per-participant rubric scores (P1-P6, 5 axes).
- [`per_category_results.csv`](per_category_results.csv) - per-category aggregates (direct answers / correct abstentions / over-abstentions / contradiction probes).
- [`thematic_codes.csv`](thematic_codes.csv) - 5 themes coded from optional one-line comments. No verbatim quotes are retained.
- [`rubric.md`](rubric.md) - formal rubric definition.
- [`consent_text.md`](consent_text.md) - participant information and consent wording.
- `packs/b3_test_full_test_pack.jsonl` - the exported annotation template the reviewers worked from.

## Aggregates reported in the dissertation

Per-axis means (and SDs) and per-category breakdowns are reported in **Table 4.9** in Section 4.10 of the dissertation. The full per-participant table is reproduced in **Table B.4** in Appendix B.10. The thematic coding is in Appendix B.10 as a paraphrased-themes table.

## Limitations

The evaluation is small (n = 6), author-facilitated rather than fully blinded, and the reviewer pool is non-domain-expert (CS peers rather than compliance specialists). Per-(participant, query) ratings were not retained, so inter-rater agreement metrics such as Cohen's kappa or Krippendorff's alpha cannot be computed from the surviving data. These caveats are explicit in Section 4.10 and in Limitation L5 (§5.2).

## Tooling (templates for follow-up evaluation)

- `scripts/export_human_eval_pack.py` exports a query / output pack for distribution to reviewers.
- `scripts/import_human_eval_pack.py` ingests reviewer-filled packs back into the evaluation pipeline; it includes Cohen's kappa computation that requires per-(reviewer, query) data not retained from the current evaluation.
