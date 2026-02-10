# Human Evaluation

## Design

A self-administered human evaluation was conducted on 20 queries sampled from the B3-Generative test run. Each query-response pair was rated on a 5-point Likert scale across three dimensions: Correctness, Groundedness, and Usefulness. The rubrics are defined in `eval/rubrics/`.

## Rater

Single rater (the author). No inter-rater agreement metrics are reported. This is acknowledged as a limitation in the dissertation (Section 4.8b, Limitation L5).

## Artifact Status

- `packs/b3_test_full_test_pack.jsonl` -- the exported annotation template (unfilled). The filled annotation was performed offline using a local copy and results are reported directly in the dissertation report (Table 4.7b).
- The tooling in `scripts/import_human_eval_pack.py` includes two-rater Cohen's kappa computation as future-work infrastructure. This capability was **not exercised** in the current evaluation — no second rater was recruited.

## Tooling

- **Export:** `python scripts/export_human_eval_pack.py --run_name <run> --split test`
- **Import (single rater):** `python scripts/import_human_eval_pack.py --run_name <run> --pack <pack.jsonl>`
- **Import (two raters, future work):** `python scripts/import_human_eval_pack.py --run_name <run> --pack <packA.jsonl> --pack_b <packB.jsonl>`

## Future Work

A production-quality evaluation would employ at least two independent raters with a formal adjudication protocol, enabling inter-annotator agreement metrics (Cohen's kappa).
