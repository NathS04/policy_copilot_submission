# Human Evaluation

## Design

An independent reviewer evaluation was conducted in two rounds, both using the same 20 query / output pairs sampled from the B3-Generative test run and the same five-axis 1-to-5 Likert rubric (**Correctness**, **Groundedness**, **Citation Usefulness**, **Usefulness**, **Trust Calibration**). The full rubric definition is in [`rubric.md`](rubric.md).

| Round | Window | Reviewers | Granularity |
| :--- | :--- | :--- | :--- |
| Round 1 | 14-18 April 2026 | P1-P6 | Per-participant aggregate (one Likert score per axis per reviewer) |
| Round 2 | April 2026 | R1-R6 | Per-(participant, query) ratings (120 ratings per axis) |

Round 2 was added so that inter-rater agreement (Krippendorff's α, ordinal-distance metric) could be computed honestly; the Round 1 aggregate could not support agreement metrics by construction.

## Reviewers

Six volunteer peer reviewers per round, recruited from the University of Leeds School of Computer Science (Final-Year BSc CS and MSc CS students), all outside the project's supervisory chain. Reviewers are referred to only as `P1`-`P6` (Round 1) and `R1`-`R6` (Round 2) with a coarse role tag (`BSc CS` / `MSc CS`); no names, emails, course codes, or other personal data are retained.

The participant information / consent text given to each reviewer is in [`consent_text.md`](consent_text.md). The Round 2 form spec used for re-collection is in [`forms/per_query_form_spec.md`](forms/per_query_form_spec.md).

## Files

| File | Contents |
| :--- | :--- |
| [`independent_review_results.csv`](independent_review_results.csv) | Round 1 per-participant rubric scores (P1-P6, 5 axes) |
| [`per_category_results.csv`](per_category_results.csv) | Round 1 per-category aggregates (direct answers / correct abstentions / over-abstentions / contradiction probes) |
| [`thematic_codes.csv`](thematic_codes.csv) | Round 1 thematic coding of optional one-line comments. No verbatim quotes retained. |
| [`anonymised_scores.csv`](anonymised_scores.csv) | Round 1 mirror, alias filename used by the evidence pack |
| [`summary_stats.csv`](summary_stats.csv) | Round 1 per-axis mean / SD / min / max |
| [`thematic_summary.md`](thematic_summary.md) | Round 1 thematic table in markdown form |
| [`per_query_raw.csv`](per_query_raw.csv) | Round 2 per-(participant, query) ratings (120 rows = 6 reviewers × 20 queries) |
| [`forms/per_query_form_spec.md`](forms/per_query_form_spec.md) | Google-Form spec for Round 2 re-collection |
| [`forms/per_query_template.csv`](forms/per_query_template.csv) | Empty long-form CSV template |
| [`rubric.md`](rubric.md) | Formal rubric definition |
| [`consent_text.md`](consent_text.md) | Participant information and consent wording |
| `packs/b3_test_full_test_pack.jsonl` | Exported annotation template the reviewers worked from |

## Aggregates reported in the dissertation

- **Round 1 per-axis means and SDs** → Table 4.9 in Section 4.10.
- **Round 1 full per-participant table** → Table B.3 in Appendix B.10.
- **Round 1 thematic coding** → paraphrased-themes table in Appendix B.10.
- **Round 2 inter-rater agreement** (Krippendorff's α with bootstrap 95% CI + binned pairwise %) → Table B.4 in Appendix B.10. The script that produces these is [`scripts/compute_human_eval.py`](../../scripts/compute_human_eval.py); it is unit-tested against the textbook edge cases in [`tests/test_compute_human_eval.py`](../../tests/test_compute_human_eval.py).

## Limitations

The evaluation is small across both rounds (n = 6 each), author-facilitated rather than fully blinded, and the reviewer pool is non-domain-expert (CS peers rather than compliance specialists). The Round 1 per-(participant, query) ratings were not retained at collection time, which is why a separate Round 2 collection was needed for agreement reporting. These caveats are made explicit in Section 4.10 and in Limitation L5 (§5.2).

## Tooling

- `scripts/compute_human_eval.py` — ingests the per-query CSV, computes per-axis statistics and Krippendorff's α with bootstrap CI; writes the evidence-pack files under `docs/evidence/human_eval/`.
- `scripts/export_human_eval_pack.py` / `scripts/import_human_eval_pack.py` — earlier per-pack tooling for distributing and re-ingesting reviewer packs.
