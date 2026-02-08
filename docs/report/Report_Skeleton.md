# Dissertation Report Skeleton

## Summary
- (Max 1 page)
- Context: Policy compliance is complex but critical.
- Problem: LLMs hallucinate and lack auditability.
- Solution: "Cited or Silent" RAG system with reliability layers.
- Results: Achieved X% precision, deployed runnable audit tool.

## Acknowledgements
- Supervisor
- University staff
- Family/friends

## Chapter 1: Introduction and Background Research

### 1.1 Introduction
- Broad context of AI in legal/policy domains.
- The shift from creative generation to factual grounding.

### 1.2 Problem Statement
- "Black box" nature of standard LLMs.
- Risk of plausible-sounding but false policy advice.
- Lack of specialized "critic" capabilities for policy drafts.

### 1.3 Aim and Objectives
- **Aim**: Build an audit-ready RAG system with >90% reliability bands.
- **Obj 1**: Construct a clean policy corpus & golden set.
- **Obj 2**: Implement "cited or silent" mechanism.
- **Obj 3**: Develop critic agent for policy language.
- **Obj 4**: Evaluate against naive RAG baselines.

### 1.4 Research Questions
- RQ1: Can citation enforcement reduce ungrounded claims?
- RQ2: How effective is a specialized critic at spotting fallacies?
- RQ3: What is the trade-off between abstention rate and accuracy?

### 1.5 Contributions
- A reproducibility-first evaluation pipeline.
- A novel "Policy Critic" module.
- Empirical benchmarks on [Specific Domain] policy documents.

### 1.6 Report Structure
- Roadmap of the following chapters.

### 1.7 Literature Review
#### 1.7.1 RAG & Long-document QA
- Evolution from TF-IDF to Dense Retrieval (DPR, FAISS).
- Context window limitations vs retrieval.
#### 1.7.2 Hallucinations & Grounded Generation
- Taxonomy of hallucination (intrinsic vs extrinsic).
- Mitigation strategies (CoT, self-consistency).
#### 1.7.3 RAG Evaluation Methods
- RAGAS, ARENA, Golden Set approaches.
- Automated vs Human eval.
#### 1.7.4 Verification/Guardrails
- Abstention mechanisms (filtering low scores).
- Entailment checking (NLI models).
#### 1.7.5 Critic/Audit of Policy Language
- NLP for fallacy detection.
- Framing analysis and normative language detection.

### 1.8 Summary of Gap
- Existing systems lack the specific "audit" workflow and strict citation requirement for high-stakes policy.

## Chapter 2: Methodology

### 2.1 Requirements & Success Criteria
- **FRs**: Ingest PDFs, Answer with citations, Abstain if unsure, Flag fallacies.
- **NFRs**: Latency < 5s, Reproducible eval, Clean code structure.
- **Success**: >30% reduction in errors vs baseline.

### 2.2 Data / Corpus Design
- Selection criteria for the ≥12 documents.
- Pre-processing steps (cleaning, chunking strategy).
- The "Internal Handbook" synthetic data for edge-case testing.

### 2.3 System Architecture
- High-level diagram (Ingest -> Index -> Retrieve -> Rerank -> Generate -> Verify).
- Component descriptions.

### 2.4 Baselines
- **B1**: Prompt-only (Zero-shot LLM).
- **B2**: Naive RAG (Simple top-k, no filters).
- **B3**: The proposed "Policy Copilot" (Full pipeline).

### 2.5 Evaluation Design
- The Golden Set (N=200).
- Split: Answerable / Unanswerable / Contradiction probes.
- Metrics: Precision/Recall for retrieval, Accuracy for abstention, Faithfulness scores.

### 2.6 Experimental Protocol
- Hardware/Software setup.
- Deterministic seed usage.
- Caching strategies for API cost management.

### 2.7 Ethical/Legal/Social/Professional Considerations
- Copyright of corpus documents.
- Bias in LLM outputs.
- "Human in the loop" necessity for policy decisions.

## Chapter 3: Implementation and Validation

### 3.1 Implementation Overview
- Tech stack: Python 3.10+, LangChain/LlamaIndex (or custom), FAISS, Streamlit.
- Repository structure explanation.

### 3.2 Ingestion & Normalisation
- PDF text extraction challenges (layout analysis).
- The stable paragraph ID system (critical for auditability).

### 3.3 Indexing & Retrieval
- Embedding model selection.
- Indexing process/hyperparameters.

### 3.4 Reranking
- Cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) rescores (query, paragraph) pairs.
- Retrieve 20 candidates from FAISS, rerank to top 5 for generation.
- Graceful fallback to retrieval scores if cross-encoder fails.

### 3.5 Evidence-Grounded Generation
- B3 prompt requires per-sentence `[CITATION: paragraph_id]` inline citations.
- Strict JSON schema enforcement with repair retry loop.
- Answer text parsed to extract sentence-level claims and their cited paragraph IDs.

### 3.6 Reliability Layer
- **Abstention Logic**: `max(top-5 rerank scores) < threshold` triggers `INSUFFICIENT_EVIDENCE`.
  Default threshold 0.30, configurable via CLI or config. Also computes `mean_top3_rerank`.
- **Per-Claim Verification**: Each sentence checked against cited paragraph(s) using Jaccard
  keyword overlap (threshold 0.10) plus numeric match bonus. If `support_rate < min_support_rate`,
  system abstains; otherwise unsupported claims are removed from the final answer.
- **Contradiction Handling**: Pairwise evidence comparison using negation/antonym pairs
  (`must` vs `must not`, `allowed` vs `forbidden`) and numeric conflict detection.
  Policy: `surface` (add note) or `abstain_on_high` (abstain on high-confidence conflicts).
- **Tier-2 LLM Verification** (optional): LLM-based claim support checking and contradiction
  judging with strict JSON prompts. Results cached to JSONL for reproducibility and cost control.
  Falls back to Tier-1 heuristics on error.

### 3.7 Critic Mode
- **Label Definitions (L1–L6)**: Normative/loaded language (L1), framing imbalance (L2),
  unsupported claims (L3), internal contradictions (L4), false dilemma (L5), slippery slope (L6).
- **Tier-1 Detection**: Lexicon-based heuristic using curated trigger lists and regex patterns.
- **Tier-2 Detection**: LLM-based classification with strict JSON output format and JSONL caching.
- **Evaluation Dataset**: 50 policy snippets (25 neutral, 25 manipulated) with ground-truth labels.
  Every label appears ≥8 times in the manipulated set. Multi-label examples included.
- **Metrics**: Per-label precision/recall/F1, macro-averaged F1, and exact match accuracy.

### 3.8 Evaluation Methodology
- **Golden Set**: 63 queries with dev/test splits (33 answerable, 20 unanswerable, 10 contradiction).
  Answerable queries require gold_paragraph_ids; contradiction probes require ≥2 conflicting IDs.
- **Human Rubric**: Groundedness (G0 binary, G1 support ratio, G2 citation correctness 0–2)
  and usefulness (U1 clarity 1–5, U2 actionability 1–5). Two-rater setup with Cohen's kappa
  for inter-rater agreement.
- **Automated Metrics**: Abstention accuracy/precision/recall, citation precision/recall,
  evidence recall@k, MRR, ungrounded claim rate.

### 3.9 UI & Audit Report Export
- Streamlit interface design.
- Export functionality for audit trails.

### 3.10 Validation & Testing
- Unit tests for core logic.
- Integration tests for the full pipeline.
- Verification of reproducibility.

## Chapter 4: Results, Evaluation and Discussion

### 4.1 Setup
- Final corpus statistics.
- Cost/Time analysis of the evaluation run.
- Golden set composition and split allocation.

### 4.2 Baseline Comparison Results
- Quantitative tables (B1 vs B2 vs B3).
- `<!-- INSERT: results/figures/fig_baselines.png -->`
- `<!-- INSERT: results/tables/run_summary.csv -->`

### 4.3 Ablation Results
- **No reranking** (`--no_rerank`): Does retrieval score ordering suffice?
- **No claim verification** (`--no_verify`): Impact on ungrounded-claim rate.
- **No contradiction detection** (`--no_contradictions`): Effect on contradictory-evidence handling.
- Each ablation produces a separate run with `summary.json` and `metrics.csv` for comparison.
- `<!-- INSERT: results/figures/fig_groundedness.png -->`
- `<!-- INSERT: results/figures/fig_tradeoff.png -->`

### 4.4 Critic Mode Results
- Per-label precision/recall/F1 table (L1–L6).
- Macro F1 and exact match accuracy.
- Comparison of Tier-1 (heuristic) vs Tier-2 (LLM) detection.
- `<!-- INSERT: results/runs/critic_*/critic_summary.json -->`

### 4.5 Human Evaluation Results
- Groundedness scores (G0, G1, G2) distribution.
- Usefulness scores (U1, U2) distribution.
- Inter-rater agreement (Cohen's kappa on G0 and binned U1).
- `<!-- INSERT: results/runs/*/human_eval_summary_test.json -->`

### 4.6 Error Analysis
- Taxonomy of remaining errors (e.g., "Missed Retrieval", "Reasoning Error").
- Qualitative examples of success/failure.

### 4.7 Discussion
- Interpretation of results in context of RQs.
- Trade-offs discovered (Speed vs Accuracy).

### 4.8 Limitations
- Domain specificity.
- Dependence on proprietary LLM APIs.

### 4.9 Conclusions
- Summary of achievements.
- Final verdict on hypothesis.

### 4.10 Future Work
- Multimodal support (Charts/Tables).
- Fine-tuning open weights models to replace APIs.

## References
- Leeds Harvard style citations.

## Appendix A: Self-Appraisal
- Reflection on the project management.
- Skills learned.
- What I would do differently.

## Appendix B: External Materials
- **B.1**: List of third-party libraries.
- **B.2**: Source document catalog.
- **B.3**: Full prompt templates.
- **B.4**: Golden set examples & marking rubrics.
- **B.5**: Original Outline Specification.
