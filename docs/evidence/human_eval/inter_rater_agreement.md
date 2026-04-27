# Inter-rater Agreement

**Status:** *Not computable from currently available data.*

**Reason:** `eval/human_eval/per_query_raw.csv` is missing or empty. Distribute the form at `eval/human_eval/forms/per_query_form_spec.md` and save the CSV export there.

## What this means

The Round 1 evaluation (P1-P6, April 2026) recorded only
per-participant aggregate Likert scores. Agreement metrics
such as Krippendorff's alpha or Fleiss' kappa require
per-(participant, query) ratings. The form spec at
`eval/human_eval/forms/per_query_form_spec.md` collects
exactly that schema; once at least 3 reviewers complete
the form, this file will be regenerated automatically by
`python scripts/compute_human_eval.py`.

## Why we don't fabricate it

Reporting a fabricated alpha (or an alpha computed from
aggregate data, which is mathematically meaningless)
would be academically dishonest. The dissertation surfaces
this as Limitation L5 (`Limited Independent Human
Evaluation`) in Section 5.2 and in Appendix B.10.
