# Golden Set v1

## Format
The golden set CSV (`golden_set.csv`) contains evaluation queries with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `query_id` | string | Unique ID (e.g., `q_001`) |
| `question` | string | The natural language question |
| `category` | enum | `answerable` \| `unanswerable` \| `contradiction` |
| `split` | enum | `dev` (tuning) \| `test` (final reporting) |
| `gold_doc_ids` | string | Comma-separated document IDs |
| `gold_paragraph_ids` | string | Comma-separated paragraph IDs (ground truth) |
| `notes` | string | Free-text annotation notes |

## Category Rules
- **answerable**: `gold_paragraph_ids` must be non-empty (1–3 IDs that answer the question)
- **unanswerable**: `gold_paragraph_ids` must be empty (topic not in corpus)
- **contradiction**: `gold_paragraph_ids` must have ≥2 IDs (the conflicting paragraphs)

## Splits
- **dev**: Used for threshold tuning, prompt iteration, and calibration. NOT used in final reported results.
- **test**: Frozen for final evaluation. Results from this split appear in the dissertation.

## Current Composition
- 33 answerable queries
- 20 unanswerable queries
- 10 contradiction probes
- Total: 63 queries

## Labelling Workflow
1. Run ingestion: `python scripts/ingest_corpus.py`
2. Build index: `python scripts/build_index.py`
3. Generate template (optional): `python scripts/make_golden_set_template.py`
4. Label gold IDs interactively: `python scripts/assist_label_gold.py --query_id q_018`
5. Validate: `python scripts/validate_golden_set.py`

## Validation
```bash
python scripts/validate_golden_set.py
```
Checks: unique IDs, valid categories/splits, gold ID rules, optional docstore cross-reference.
