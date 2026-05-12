# Contribution Map

This project's contribution is not a new foundation model. It is an evaluated
reliability layer for policy-document retrieval-augmented generation (RAG).
The system, evaluation harness, evidence pack, and report are all the author's
own work, in line with the AI usage declaration in Appendix B.5 of the report.

## Built by the author

- PDF and paragraph ingestion pipeline with stable, deterministic paragraph
  identifiers (`doc_id::page::index::hash`).
- Retrieval wrapper that supports both dense (FAISS bi-encoder) and BM25
  backends, with explicit per-run provenance recording.
- Cross-encoder reranking integration and a deterministic fallback path
  used when the reranker model is unavailable.
- Abstention gate that uses the cross-encoder confidence signal, with the
  threshold tuned on the validation split.
- Pydantic-enforced answer schema and repair-and-retry handling for
  malformed LLM JSON output.
- Sentence-level claim splitting and per-claim Jaccard token-overlap
  citation verification.
- Numeric and token-overlap consistency checks for cited evidence.
- Cross-paragraph contradiction surfacing with policy-driven response
  modification.
- Extractive Fallback Mode that bypasses the LLM entirely and returns the
  cited paragraph verbatim.
- Heuristic Critic Mode with six pattern categories and a labelled
  evaluation suite.
- Streamlit audit workbench with six discoverable modes: Ask, Audit Trace,
  Critic Lens, Experiment Explorer, Reviewer Mode, Help & Guide.
- Reviewer Mode supporting structured peer evaluation with anonymised
  per-query rating capture and CSV export.
- Evaluation scripts producing JSONL/CSV outputs, headline tables, and
  figures used in the dissertation.
- Public Guidance Transfer Corpus ingestion pipeline, with provenance,
  licence (OGL v3.0), retrieval dates, and content hashes recorded.
- Adversarial probe harness with paired extractive/generative runs and
  per-attack-type breakdown.
- One-click audit export bundle (JSON, HTML, Markdown).
- Reproducibility scripts and a whitelist-based clean-submission ZIP
  builder with a forbidden-path validator.

## Third-party components

- LLM APIs (OpenAI, optionally Anthropic) used for generation where a key
  is configured.
- Open-source Python libraries listed in Appendix B.1 (FAISS, Sentence
  Transformers, Pydantic, pypdf, pdfplumber, Streamlit, pytest, etc.).
- Public Guidance Transfer Corpus content from NCSC, ICO, and ACAS,
  redistributed under the Open Government Licence v3.0.

## Main research contribution

The project evaluates whether deterministic citation enforcement, a
confidence-gated abstention rule, and post-generation claim verification
together reduce unsupported claims in policy-document RAG, and surfaces
the resulting reliability/helpfulness trade-off through a baseline ladder,
ablations, a public-transfer stress test, a small independent reviewer
evaluation, and an adversarial probe.

## Main limitation

The strongest quantitative evidence is still from a synthetic primary
benchmark authored for this project. The public-transfer stress test is
small (20 queries, 8 documents) and runs in Extractive Mode only.
Reviewer evaluation used Computer Science peers (n = 6) rather than
compliance professionals. A publishable follow-up would address each of
these in turn; the current dissertation deliberately stops short of that
claim and frames the system as the experimental harness rather than the
final evidence base.
