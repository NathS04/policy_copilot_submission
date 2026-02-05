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
