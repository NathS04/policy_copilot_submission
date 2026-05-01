# Public Guidance Transfer Stress Test

This folder holds the per-query failure taxonomy for the Public Guidance Transfer Stress Test reported in Section 4.11 of the dissertation.

## What this is

A 20-query stress test against a **small public-guidance corpus** (8 documents, 249 paragraphs, all under OGL v3.0) drawn from:

- National Cyber Security Centre (NCSC),
- Information Commissioner's Office (ICO),
- Advisory, Conciliation and Arbitration Service (ACAS).

The corpus and its provenance live separately at `data/public_transfer_corpus/`. The test was **not** used to tune any threshold or training decision in the main benchmark; it is a one-shot probe of whether the safety properties (citation precision, ungrounded rate) survive a corpus shift to text the author did not write.

## Files

| File | Content |
| :--- | :--- |
| `failure_taxonomy.csv` | One row per query: query metadata, system status, top-3 retrieved paragraph IDs, auto-assigned label, hand-confirmed final label, short explanation |

The categories are deterministic and produced by `scripts/build_failure_taxonomy.py`:

```
clean_answer / retrieval_miss / terminology_mismatch /
long_guidance_page / weak_obligation / over_abstention /
out_of_scope / unanswerable_attempted /
ambiguous_handled / ambiguous_abstained / other
```

The corresponding human-readable narrative (method, summary table, three representative examples, interpretation, limitations) is at `docs/evidence/verification/public_transfer_failure_taxonomy.md`.

## How to regenerate

```bash
python scripts/build_failure_taxonomy.py
```

Re-runs the taxonomy from the per-query records under `results/runs/b3_extractive_public_transfer/outputs.jsonl` and the gold annotations under `eval/golden_set/public_transfer_set.csv`. No new system runs are performed.

## Limitations

- The corpus is small (8 documents) and the query set is small (20 queries); the taxonomy is descriptive rather than statistically representative.
- Extractive Mode only; the corresponding generative-mode transfer test is listed as future work in §5.3.
- Hand-confirmed labels match auto-labels in the current pass; the CSV preserves both columns so a reviewer can audit the labelling.
