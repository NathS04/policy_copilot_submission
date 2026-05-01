# Public Guidance Transfer Corpus

A small public-guidance corpus used **only** for the §4.11 Public Guidance Transfer Stress Test. Not used for training, threshold tuning, or any decision in the main benchmark.

## Sources

All sources are published under the **Open Government Licence v3.0**, which permits reuse with attribution. No third-party copyrighted material is included.

| Publisher | Topic | Theme |
| :--- | :--- | :--- |
| National Cyber Security Centre (NCSC) | BYOD guidance | IT security |
| National Cyber Security Centre (NCSC) | Mobile device security | IT security |
| Information Commissioner's Office (ICO) | Data protection principles | Data protection |
| Information Commissioner's Office (ICO) | Lawful basis for processing (UK GDPR) | Data protection |
| Information Commissioner's Office (ICO) | Individual rights (UK GDPR) | Data protection |
| Advisory, Conciliation and Arbitration Service (ACAS) | Disciplinary procedure | Employment |
| Advisory, Conciliation and Arbitration Service (ACAS) | Holiday entitlement and pay | Employment |
| Advisory, Conciliation and Arbitration Service (ACAS) | Working from home / hybrid working | Employment |

Total: 8 documents, 249 paragraphs.

## Files

| Path | Content |
| :--- | :--- |
| `raw/` | One `.txt` file per source (main article body only; navigation / footers / cookie banners stripped) |
| `processed/paragraphs.jsonl` | Stable `paragraph_id`, `doc_id`, page, text — same chunking pipeline as the synthetic corpus |
| `provenance.csv` | Per-source URL, retrieval timestamp, included sections, paragraph count, twelve-character content hash |

## How the downloader works

```bash
python scripts/download_public_corpus.py    # fetches HTML, extracts main body, writes raw/ + provenance.csv
python scripts/ingest_public_corpus.py       # chunks raw/ into processed/paragraphs.jsonl
```

The downloader is idempotent: re-running it overwrites `raw/` and `provenance.csv` with fresh retrievals. Content hashes in `provenance.csv` are the canonical record of what was used in the dissertation; if a public source has been edited since the recorded retrieval timestamp, the cached `raw/` text is still the version the §4.11 numbers refer to.

## Personal data

None. NCSC, ICO, and ACAS guidance pages do not contain personal data; their published terms confirm Crown copyright with reuse permitted under OGL v3.0.

## Reproducing §4.11

```bash
python scripts/run_transfer_eval.py
```

Runs B3-Extractive against the public corpus using the 20-query test set in `eval/golden_set/public_transfer_set.csv`. Results are written to `results/runs/b3_extractive_public_transfer/`.
