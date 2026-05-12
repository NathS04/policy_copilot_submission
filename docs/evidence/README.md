# Evidence Pack

This directory is the single discoverable entry point for an examiner who
wants to verify the claims made in the dissertation against the artefacts
in this repository. Every claim that is referenced in the report has a
file under this directory, or a pointer from here to where the file lives.

## Layout

```
docs/evidence/
├── README.md            <- this file
├── checklist.md         <- one-row-per-claim mapping: claim → evidence file
├── capture_guide.md     <- how each artefact was produced and how to regenerate it
└── human_eval/          <- materials and results for the Section 4.10 evaluation
    ├── participant_info.md
    ├── consent_text.md
    ├── rubric.md
    ├── anonymised_scores.csv
    ├── summary_stats.csv
    └── thematic_summary.md
```

The `human_eval/` files mirror the working copies under `eval/human_eval/`
so that an examiner only has to look in one place.

## How to use this folder

1. Start with `checklist.md`. It lists every substantive claim in
   Chapters 4 and 5 of the dissertation alongside the artefact file that
   evidences the claim. If a claim is missing from the checklist, treat
   that as a documentation gap to flag.
2. For each artefact, `capture_guide.md` records who produced it, when,
   and how it can be reproduced. Reproduction commands are scoped to the
   project's `.venv` and assume the standard install in
   `INSTRUCTIONS_FOR_EVALUATOR.md`.
3. `human_eval/` is the Independent Reviewer Evaluation pack referenced
   from Section 4.10 and Appendix B.10. The data is anonymised at
   collection time; reviewers are referred to only as `P1`-`P6` with a
   role tag (`BSc CS` or `MSc CS`).

## What is *not* in this folder

- Raw participant identifiers (names, emails, course identifiers) are
  not retained. Anonymisation is at collection time, not after the
  fact.
- Verbatim free-text reviewer comments are not retained. Comments are
  reported only as paraphrased themes (`thematic_summary.md`).
- LLM API keys, run configs containing secrets, or anything tied to a
  specific test machine. Reproduction commands assume a clean
  consumer-laptop install.

## Pointers to other parts of the repository

- `results/runs/` - per-run JSON / CSV / `outputs.jsonl` for every
  evaluation reported in the dissertation, including the
  `b3_extractive_public_transfer` run that supports Section 4.11.
- `data/public_transfer_corpus/` - the OGL-licensed NCSC + ICO + ACAS
  corpus and its provenance file (referenced from Appendix B.11).
- `eval/golden_set/golden_set.csv` and `public_transfer_set.csv` -
  the synthetic and transfer query sets.
- `tests/` - the 195 automated tests that validate the reproducibility
  contract.
