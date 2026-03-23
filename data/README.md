# Data Directory

This directory contains the corpus and supplementary materials for the Policy Copilot.

## Corpus Structure

- `corpus/raw/`: Original PDF documents. **Not tracked in git**.
- `corpus/processed/`: Extracted text and metadata in JSONL/CSV format. **Not tracked in git**.
- `corpus/manifests/`: Metadata about the corpus (titles, authors, publication dates).

## Processed Data Format

The ingestion pipeline produces `processed_corpus.jsonl` where each line is a JSON object representing a paragraph:

```json
{
  "doc_id": "unique_doc_id",
  "paragraph_id": "doc_id_p_123",
  "text": "The actual text content...",
  "page_number": 42,
  "section_title": "Section 3.1",
  "source_file": "document_name.pdf"
}
```

## Internal Handbook

Located in `handbook/`, this is a synthetic document created for this project to test specific edge cases.

- `internal_handbook_v1.md`: The base version.
- `variants/neutral/`: A neutral phrasing of the policy.
- `variants/manipulated/`: Versions with inserted fallacies or normative language for testing the Critic.
