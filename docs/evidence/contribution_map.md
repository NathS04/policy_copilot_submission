# Contribution Map

Policy Copilot is a conservative policy-document QA system. It is not designed
to answer every question; it is designed to answer only when the supporting
policy evidence is strong enough to cite. The project wraps standard RAG with
paragraph-level citations, reranking, abstention, claim-level verification,
contradiction surfacing, Extractive Mode, and audit exports. The main finding
is the safety/coverage trade-off: stricter evidence checks reduce unsupported
answers, but they also reduce how often the system is willing to answer. I
evaluate that trade-off using baselines, ablations, reviewer feedback, a small
public-guidance transfer test, adversarial probes, and a reproducible evidence
pack.

The contribution is not a new foundation model. It is an evaluated reliability
layer for policy-document RAG. The system, evaluation harness, evidence pack,
and report are all the author's own work, in line with the AI usage declaration
in Appendix B.5 of the report.

## Core contribution and extensions

| Layer | Role in the project | Evidence |
| :--- | :--- | :--- |
| Core CS problem | Closed-corpus policy QA is risky when systems give fluent answers without evidence. The project asks whether citation enforcement, abstention, and per-claim verification can make RAG safer to audit. | Chapter 1; `docs/evidence/checklist.md` |
| Core implementation | Ingestion with stable paragraph IDs, retrieval (BM25 / dense), cross-encoder reranking, schema-validated generation, sentence-level claim verification, abstention, contradiction surfacing. | `src/policy_copilot/`; `tests/`; `results/runs/` |
| Core evaluation | B1, B2, and B3 compared on the held-out golden set using retrieval, citation, groundedness, and abstention metrics. | Chapter 4; `results/tables/run_summary.csv`; `results/manifest.json` |
| Reliability extension | Extractive Mode tests the safest version of the design by returning the cited paragraph directly rather than a free-form answer. | `results/runs/b3_extractive_final/`; Chapter 4 |
| Human-check extension | Peer reviewers provide a small supporting check on whether outputs felt correct, grounded, and appropriately cautious. | Appendix B.10; `docs/evidence/human_eval/` |
| Externality extension | Public-guidance transfer checks the extractive system on documents that were not written for the synthetic benchmark. | Appendix B.11; `data/public_transfer_corpus/`; `eval/public_transfer/` |
| Robustness extension | Adversarial probes check whether prompt-injection style inputs make the extractive system fabricate citations or unsupported answers. | Appendix B.12; `eval/adversarial/` |
| Examiner-usability extension | Audit exports, the case-study walkthrough, and the evidence pack map every headline claim to a concrete file and command. | `docs/evidence/`; `INSTRUCTIONS_FOR_EVALUATOR.md`; `docs/evidence/verification/vertical_slice_case_study.md` |

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
- Public Guidance Transfer Corpus: cached main text from NCSC, ICO and
  ACAS guidance pages whose site terms or page footers state Open
  Government Licence v3.0, except where otherwise stated. Provenance,
  retrieval dates, and content hashes are recorded in
  `data/public_transfer_corpus/provenance.csv`.

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
