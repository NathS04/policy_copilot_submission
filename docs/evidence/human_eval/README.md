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
| `anonymised_scores.csv` | Per-participant aggregate scores. Six rows (P1-P6), seven columns. |
| `summary_stats.csv` | Per-axis mean / SD / min / max computed from `anonymised_scores.csv`. |
| `thematic_summary.md` | Five themes paraphrased from optional one-line comments. No verbatim quotes. |

## Schema of `anonymised_scores.csv`

```
participant_id,role,correctness,groundedness,citation_usefulness,usefulness,trust_calibration
P1,MSc CS,5,5,4,4,5
...
```

The CSV is at **per-participant aggregate granularity** (one row per
participant, mean across the 20 outputs they scored). Per-(participant,
query) rows were not retained at collection time; this is documented as
**Limitation L5** in §5.2 of the dissertation. As a consequence,
inter-rater agreement metrics such as Cohen's kappa or Krippendorff's
alpha cannot be computed from the surviving data. A production-quality
follow-up evaluation would store per-(participant, query) rows so that
agreement can be measured.

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
