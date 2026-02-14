# Audit-Ready Policy Copilot: Evidence-Grounded RAG with Reliability Controls

**Nathan [Surname]**

Submitted in accordance with the requirements for the degree of BSc Computer Science

2024/25

COMP3931 Individual Project

---

## Summary

Organisations depend on internal policy documents — handbooks, security addenda, compliance checklists — to govern day-to-day operations. Employees frequently need answers to policy questions ("How many days can I work remotely?", "What is the password rotation period?"), yet manual search is slow and error-prone. Large Language Models (LLMs) offer fluent answers but suffer from hallucination, posing unacceptable risks in compliance-sensitive domains.

This project presents **Policy Copilot**, a Retrieval-Augmented Generation (RAG) system engineered for high-stakes environments. The system enforces a strict **"cited or silent"** guarantee: every claim in the response is anchored to a specific source paragraph, and the system abstains when evidence is insufficient rather than guessing.

The architecture introduces three layers of reliability control absent from naïve RAG:
1.  **Cross-encoder reranking** to improve retrieval precision and provide a calibrated confidence signal.
2.  **Per-claim citation verification** using deterministic heuristics to prune unsupported statements.
3.  **Contradiction detection** to identify conflicting policy directives across documents.
4.  An explicit **Extractive Fallback Mode** that ensures functionality even when the LLM is unavailable, returning top-ranked evidence directly.

Evaluation on a 63-query golden set demonstrates that the full system (B3) achieves a **92% answer rate** on answerable queries while maintaining **58% abstention accuracy** on unanswerable queries in its generative configuration. In strict extractive mode, the system successfully reverts to direct evidence retrieval, maintaining 100% citation precision. Ablation studies confirm that reranking is the primary driver of reliability. Additionally, a heuristic **Critic Mode** achieves 93.8% macro F1 score in auditing policy text for vague or contradictory language.

The project concludes that lightweight, deterministic reliability controls can significantly improve the trustworthiness of RAG systems, making them viable for automated policy compliance.

---

## Acknowledgements

I would like to thank my supervisor for their guidance and feedback throughout this project. I would also like to thank the module coordinators for COMP3931 for providing clear expectations and resources.

*Note: No proofreading assistance was sought or received beyond standard word-processing tools (spell check). All writing is my own.*

---

## Table of Contents

- [Summary](#summary)
- [Acknowledgements](#acknowledgements)
- [Chapter 1: Introduction and Background Research](#chapter-1-introduction-and-background-research)
- [Chapter 2: Methodology](#chapter-2-methodology)
- [Chapter 3: Implementation and Validation](#chapter-3-implementation-and-validation)
- [Chapter 4: Results, Evaluation and Discussion](#chapter-4-results-evaluation-and-discussion)
- [List of References](#list-of-references)
- [Appendix A: Self-appraisal](#appendix-a-self-appraisal)
- [Appendix B: External Materials](#appendix-b-external-materials)

---

## Chapter 1: Introduction and Background Research

### 1.1 Introduction

Internal policy documents — employee handbooks, IT security addenda, data protection guidelines — are essential governance tools in any organisation. When employees need answers to policy questions, they face two problems: finding the right document and extracting the correct answer. Manual search is slow, inconsistent, and scales poorly as document volumes grow.

Large Language Models (LLMs) can generate fluent natural-language answers, but they are prone to **hallucination**: generating plausible-sounding but factually unsupported statements. In compliance-sensitive domains, a hallucinated policy answer could lead to regulatory violations, data breaches, or disciplinary consequences.

The core research question motivating this project is:
> *Can we build a question-answering system over policy documents that is reliably grounded in source evidence, and that knows when to stay silent rather than guess?*

### 1.2 Aims and Objectives

The aim of this project is to develop and evaluate an **Audit-Ready Retrieval-Augmented Generation (RAG)** system for organisational policy documents.

**Objectives:**
1.  **Build a RAG system** that answers policy questions only when supported by cited evidence (Target: ungrounded answer rate ≤ 5%).
2.  **Implement abstention** mechanisms so the system refuses to answer when evidence is insufficient (Target: abstention accuracy ≥ 80% on unanswerable queries).
3.  **Achieve high retrieval quality** through dense retrieval with cross-encoder reranking (Target: evidence recall@5 ≥ 80%).
4.  **Detect contradictions** between policy documents and surface them to the user.
5.  **Develop a Critic Mode** to audit policy text for problematic language patterns.
6.  **Evaluate systematically** using a golden set with automated metrics, comparing generative (LLM) and extractive (non-LLM) modes.

### 1.3 Systematic Search Strategy

To ensure a comprehensive background review, a systematic search was conducted using Google Scholar, ACM Digital Library, and arXiv.

-   **Keywords**: "Retrieval-Augmented Generation", "LLM Hallucination Mitigation", "Fact Verification", "RAG Evaluation", "Policy Question Answering".
-   **Inclusion Criteria**: Papers published 2020-2024 (post-GPT-3), focusing on grounded generation, citation enforcement, or legal/policy domains.
-   **Review Process**: Initially 40+ papers were identified; 15 were selected for detailed review based on relevance to the "cited or silent" reliability problem.

### 1.4 Background Research and Related Work

#### 1.4.1 Retrieval-Augmented Generation (RAG)
RAG (Lewis et al., 2020) decomposes QA into retrieval and generation. Standard RAG uses dense retrieval (Karpukhin et al., 2020) to find relevant passages, which are then passed to the LLM. While effective for knowledge-intensive tasks, standard RAG lacks explicit verification, leading to "hallucination loops" where the model ignores retrieved context or misinterprets it.

#### 1.4.2 Hallucination and Attribution
Ji et al. (2023) survey hallucination in NLG, identifying it as the primary barrier to adoption in high-stakes fields. Recent work focuses on **attribution**:
-   **Attributed QA** (Bohnet et al., 2022) requires models to cite sources.
-   **RARR** (Gao et al., 2023) retroactively edits claims to match evidence.
-   **Self-RAG** (Asai et al., 2024) trains the LLM to output reflection tokens (e.g., `[Retrieve]`, `[Relevant]`).

#### 1.4.3 Comparison of Approaches
The table below situates Policy Copilot against existing approaches.

| Approach | Corpus Type | Grounding Method | Evaluation Focus | Limitations | Relevance to Project |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard RAG** (Lewis et al., 2020) | Open Domain (Wiki) | Implicit (Context Injection) | Answer Accuracy | No citation guarantees; hallucinates freely | Baseline (B2) |
| **Attributed QA** (Bohnet et al.) | Open Domain | Training-based citation | Citation Recall | Requires fine-tuning; not explicitly verifiable | Conceptual inspiration |
| **RARR** (Gao et al., 2023) | Open Domain | Post-hoc editing (LLM) | Attribution | High latency; expensive (multiple LLM calls) | Verification logic |
| **Self-RAG** (Asai et al., 2024) | Open Domain | Training (Reflection tokens) | Generation Quality | Complex training pipeline; overkill for closed corpus | Verification logic |
| **Policy Copilot** (This Project) | **Closed Domain (Policy)** | **Deterministic Verification** | **Reliability & Abstention** | **Strict scope; conservative** | **Proposed Solution** |

#### 1.4.4 Gap Analysis
Existing work largely focuses on *open-domain* QA, where broad coverage is prioritized and slight inaccuracies are tolerable. There is a gap in **closed-domain, high-stakes policy QA**, where:
1.  **Precision > Recall**: It is better to answer nothing than to answer incorrectly.
2.  **Auditability**: Every answer needs a precise paragraph-level citation.
3.  **Conflict Detection**: Policies often contradict each other (e.g., Group policy vs. Local addendum), a problem rarely addressed in standard RAG benchmarks.

Policy Copilot addresses this gap by implementing a "safety-first" architecture with deterministic reliability layers.

---

## Chapter 2: Methodology

### 2.1 Development Process
The project followed an iterative, agile-like methodology with six distinct phases:
1.  **Corpus Engineering**: Creating synthetic policy documents and an ingestion pipeline.
2.  **Retrieval Pipeline**: Implementing FAISS indexing and Dense Retrieval.
3.  **Generative Pipeline**: Integrating LLMs with prompt engineering for JSON output.
4.  **Reliability Layers**: Adding Reranking (Cross-encoder), Verification, and Contradiction detection.
5.  **Critic Mode**: Developing the heuristic policy auditor.
6.  **Rigorous Evaluation**: Creating the Golden Set, implementing Extractive Fallback, and conducting ablation studies.

### 2.2 Requirements Analysis
The system was designed to meet the following Functional (FR) and Non-Functional (NFR) requirements.

| ID | Requirement | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- |
| **FR1** | **Evidence Grounding** | All answers must cite specific paragraph IDs. | High |
| **FR2** | **Abstention** | System returns `INSUFFICIENT_EVIDENCE` if confidence < threshold. | High |
| **FR3** | **Citation Verification** | Claims not supported by cited text are removed. | High |
| **FR4** | **Extractive Fallback** | System functions without LLM if enabled, returning raw text. | Medium |
| **FR5** | **Conflict Detection** | Contradictions between documents are flagged. | Medium |
| **NFR1** | **Latency** | End-to-end response time < 10 seconds (P95). | Medium |
| **NFR2** | **Reproducibility** | Evaluation pipeline is deterministic and scriptable. | High |
| **NFR3** | **Modularity** | Components (Reranker, Verifier) can be toggled via config. | Low |

### 2.3 System Architecture
The system follows a modular "Retrieve-and-Rerank-then-Generate-and-Verify" pipeline.

*[Placeholder: Figure 2.1 - System Architecture Diagram showing the flow: Query -> Retriever -> Reranker -> LLM -> Verifier -> Output]*

1.  **Ingestion**: PDFs are chunked into paragraphs and assigned stable IDs.
2.  **Retrieval**: Bi-encoder finds top-20 candidates from FAISS index.
3.  **Reranking**: Cross-encoder scores query-candidate pairs for precise relevance.
4.  **Generation**: LLM constructs an answer with citations (Generative Mode) OR top paragraph is returned (Extractive Mode).
5.  **Verification**: Heuristic checks ensure claims match evidence.
6.  **Response**: The final verified answer or an abstention message is returned.

### 2.4 Design Decisions and Alternatives Considered

**Decision 1: RAG vs. Long-Context Window**
*Alternative*: Dumping all 53 pages of policy into the context window of a >100k context model (e.g., Claude 3).
*Why Rejected*: Long-context models suffer from "lost-in-the-middle" phenomena (Liu et al., 2023) and are expensive per query. RAG is more scalable and forces explicit selection of evidence.

**Decision 2: Dense Retrieval + Reranking vs. Sparse Retrieval (BM25)**
*Alternative*: Using simple keyword search (BM25).
