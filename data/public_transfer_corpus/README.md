# Public Guidance Transfer Corpus

A small public-guidance corpus used **only** for the §4.11 Public Guidance Transfer Stress Test. Not used for training, threshold tuning, or any decision in the main benchmark.

## Sources

The captured text used in this corpus was taken from public-sector guidance pages whose site terms or page footers state **Open Government Licence v3.0**, except where otherwise stated. The downloader keeps only main article text and excludes logos, images, navigation, cookie banners, and other non-text or third-party material. No third-party copyrighted material is included.

The ACAS flexible-working row is a known caveat: the recorded target URL `https://www.acas.org.uk/working-from-home-and-hybrid-working` resolved at retrieval time to broader Acas flexible-working content (page title "Flexible working | Acas"). The cached raw text under `raw/acas_remote_hybrid_working.txt` and its content SHA-256 in `provenance.csv` preserve the exact text that was used in the §4.11 stress test, so no metric is affected; the row title in `provenance.csv` was relabelled "Flexible-working guidance including home/hybrid material" to match what was actually captured.

| Publisher | Topic | Theme |
| :--- | :--- | :--- |
| National Cyber Security Centre (NCSC) | BYOD guidance | IT security |
| National Cyber Security Centre (NCSC) | Password administration | IT security |
| Information Commissioner's Office (ICO) | Data protection principles | Data protection |
| Information Commissioner's Office (ICO) | Lawful basis for processing (UK GDPR) | Data protection |
| Information Commissioner's Office (ICO) | Individual rights (UK GDPR) | Data protection |
| Advisory, Conciliation and Arbitration Service (ACAS) | Disciplinary procedure | Employment |
| Advisory, Conciliation and Arbitration Service (ACAS) | Holiday entitlement and pay | Employment |
| Advisory, Conciliation and Arbitration Service (ACAS) | Flexible-working guidance (incl. home/hybrid material) | Employment |

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
