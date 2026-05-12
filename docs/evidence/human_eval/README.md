# Independent Reviewer Evaluation: Evidence Pack

This folder is the single discoverable copy of the materials and
anonymised results for the independent reviewer evaluation reported in
Section 4.10 of the dissertation. It mirrors the working copies in
`eval/human_eval/`.

## Files

| File | Purpose |
| :--- | :--- |
| `participant_info.md` | The information sheet shown to participants before they consented. |
| `consent_text.md` | The full consent wording. |
| `rubric.md` | The 1-to-5 Likert rubric across five axes (Correctness, Groundedness, Citation Usefulness, Usefulness, Trust Calibration). |
| `anonymised_scores.csv` | Round 1 per-participant aggregate scores (P1-P6). |
| `per_query_anonymised_scores.csv` | Round 2 per-(reviewer, query) scores from 6 independent reviewers (R1-R6) x 20 queries. |
| `summary_stats.csv` | Per-axis mean / SD / min / max computed from `anonymised_scores.csv`. |
| `per_query_summary_stats.csv` | Per-axis summary stats computed from the Round 2 per-query data. |
| `inter_rater_agreement.md` | Krippendorff alpha results from Round 2, with 95% CI and pairwise % agreement. |
| `thematic_summary.md` | Five themes paraphrased from optional one-line comments. No verbatim quotes. |

## Schema of `anonymised_scores.csv`

```
participant_id,role,correctness,groundedness,citation_usefulness,usefulness,trust_calibration
P1,MSc CS,5,5,4,4,5
...
```

`anonymised_scores.csv` is the Round 1 file at **per-participant aggregate
granularity** (one row per participant, mean across the 20 outputs they
scored). Round 1 did not retain per-(participant, query) rows.

Round 2 was added to address that gap: `per_query_anonymised_scores.csv`
contains 120 rows (6 reviewers x 20 queries) so that inter-rater
agreement can be computed. Krippendorff's alpha is reported per axis in
`inter_rater_agreement.md` and discussed in Section 4.10 and Appendix B.10
of the dissertation.

## Anonymisation

- Participants were assigned the labels `P1`-`P6` and a coarse role tag
  (`BSc CS` or `MSc CS`) **before any data was stored**.
- No name, email, course code, or other personal identifier was ever
  written to the dataset.
- Free-text comments were coded into themes after the evaluation closed
  (18 April 2026) and are not retained verbatim. `thematic_summary.md`
  contains paraphrased observations only.

## How to reproduce the aggregates

The numbers in `summary_stats.csv` can be recomputed from
`anonymised_scores.csv` directly:

```bash
python -c "
import csv, statistics
rows = list(csv.DictReader(open('anonymised_scores.csv')))
for axis in ['correctness','groundedness','citation_usefulness','usefulness','trust_calibration']:
    vals = [int(r[axis]) for r in rows]
    print(axis, round(statistics.mean(vals), 2), round(statistics.stdev(vals), 2))
"
```

The dissertation's Section 4.10 Table 4.9 and Appendix B.10 Table B.4
are produced from the same source.
