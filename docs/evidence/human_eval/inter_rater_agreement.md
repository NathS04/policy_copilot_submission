# Inter-rater Agreement

**Status:** Computed from 6 reviewers x 20 queries x 5 axes.

## Method

Inter-rater agreement is reported as **Krippendorff's alpha**
with the ordinal-distance metric appropriate for 1-5 Likert
ratings (Krippendorff, 2004). Bootstrap 95% confidence intervals
are obtained by resampling items with replacement (1,000
iterations, seed = 42). As a non-parametric robustness check we
also report binned pairwise % agreement after the mapping
{1-2 -> low, 3 -> mid, 4-5 -> high}.

All metrics are computed by `scripts/compute_human_eval.py`,
which is committed alongside the data and tested against the
Krippendorff (2004) example dataset (see `tests/`).

## Results

| Axis | Krippendorff alpha | 95% CI | Pairwise % (binned) |
| :--- | :---: | :---: | :---: |
| Correctness | 0.745 | [0.467, 0.867] | 86% |
| Groundedness | 0.256 | [0.072, 0.404] | 100% |
| Citation Usefulness | 0.339 | [0.102, 0.502] | 86% |
| Usefulness | 0.733 | [0.447, 0.848] | 80% |
| Trust Calibration | 0.745 | [0.469, 0.868] | 86% |

## Interpretation

Krippendorff (2004) suggests informal cut-offs of alpha >= 0.80
for confident interpretation, alpha >= 0.667 for tentative
interpretation, and alpha < 0.667 as evidence that the
underlying rating task is too noisy for strong claims. The
values above are reported honestly without normative
framing; the dissertation (Section 4.10 and Appendix B.10)
discusses what the observed alpha implies for the
trustworthiness of the per-axis means.

## Limitations

- Sample is small (n = 6 reviewers).
- Reviewers are technically literate CS peers, not domain
  specialists in compliance or policy.
- The author is identifiable as the recruiter, so the
  evaluation is author-facilitated rather than fully
  blinded.
- Per-query results are reported in the report (Appendix
  B.10) and the raw per-query rows are in
  `docs/evidence/human_eval/anonymised_scores.csv`.
