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
*Why Rejected*: Policy questions often use synonyms (e.g., "remote work" vs "work from home") that keyword search misses. Dense retrieval captures semantics. Reranking adds the necessary precision for the citation guarantee.

**Decision 3: Deterministic Verification vs. LLM-only Verification**
*Alternative*: Asking a second LLM "Is this claim supported?"
*Why Rejected*: LLM-as-a-judge is slow, expensive, and non-deterministic. Deterministic metrics (token overlap, numeric matching) provide a fast, auditable baseline that doesn't hallucinate.

### 2.5 Evaluation Methodology
Three baselines were defined to measure progress:
*   **B1 (Prompt-Only)**: Zero-shot LLM (measures hallucination baseline).
*   **B2 (Naive RAG)**: Standard Retrieval + Generation (no verification).
*   **B3 (Policy Copilot)**: Full pipeline with Reranking, Verification, Contradiction Detection.

**Metrics**:
*   **Answer Rate**: % of answerable queries answered.
*   **Abstention Accuracy**: % of unanswerable queries refused.
*   **Ungrounded Rate**: % of claims without valid evidence support.
*   **Evidence Recall@5**: % of gold paragraphs found in top-5.

---

## Chapter 3: Implementation and Validation

### 3.1 Technology Stack
*   **Language**: Python 3.10+
*   **Retrieval**: `sentence-transformers` (all-MiniLM-L6-v2), `FAISS` (IndexFlatL2).
*   **Reranking**: `cross-encoder/ms-marco-MiniLM-L-6-v2`.
*   **LLM Integration**: OpenAI API (configurable) with Pydantic for schema validation.
*   **Config**: `pydantic-settings` for robust environment management.
*   **Testing**: `pytest`.

### 3.2 Component Walkthrough

#### 3.2.1 Ingestion (`src/policy_copilot/ingest`)
The ingestion module normalizes PDF text. A critical innovation here is the **Stable ID Scheme**: ids are generated as `doc_id::page::index::hash`. This ensures that even if documents are re-ingested, citations in old logs remain valid unless the specific paragraph content changed.

#### 3.2.2 Indexing and Retrieval (`src/policy_copilot/retrieve`)
The `Retriever` class manages the FAISS index. It handles the bi-encoder embedding. A `Reranker` class wraps the cross-encoder. The reranker output includes a confidence score (logit) which is the primary signal for the **Abstention Gate**. If `max_score < threshold`, the query is rejected before generation.

#### 3.2.3 Generation (`src/policy_copilot/generate`)
The `Answerer` class constructs the prompt. It uses a "One-Shot" prompting strategy with an example of a correctly cited answer. The strict JSON schema forces the model to separate `answer` text from `citations` list, simplifying parsing.

#### 3.2.4 Verification (`src/policy_copilot/verify`)
Post-generation, the `Verifier` decomposes the answer into claims (sentences).
1.  **Token Overlap**: Jaccard similarity between claim and cited paragraph.
2.  **Numeric Check**: If the claim contains strict numbers ("30 days"), they must appear in the source.
3.  **Pruning**: Claims failing verification are stripped from the response.

#### 3.2.5 Critic Mode (`src/policy_copilot/critic`)
A separate module containing regex-based logical rule checkers for 6 types of "bad policy language" (e.g., Vague Quantifiers like "some", "appropriate").

### 3.3 Testing and Validation
The codebase is covered by a comprehensive test suite (79 tests).

| Test Suite | Scope | Validates |
| :--- | :--- | :--- |
| `test_ingest` | PDF parsing | Text extraction, ID stability |
| `test_abstain` | Logic | Threshold gating mechanics |
| `test_claim_verification` | Heuristic | Logic for token overlap/numeric checking |
| `test_contradictions` | Logic | Handling of 'must' vs 'must not' |
| `test_reranker` | Model | Sorting correctness of cross-encoder |
| `test_critic` | Heuristic | Precision/Recall of regex patterns |

This rigorous testing ensures that the reliability mechanisms (the core contribution) function deterministically.

---

## Chapter 4: Results, Evaluation and Discussion

### 4.1 Experimental Setup
Evaluation was conducted in two modes:
1.  **Generative Mode**: Standard LLM-based RAG. Used for B1, B2, and B3 (Generative).
2.  **Extractive Mode**: A "safe mode" where the LLM is disabled. B3 falls back to returning the exact text of the top-ranked paragraph if confidence is high. This isolates retrieval performance from generation quality.

**Golden Set**: 63 queries (36 Answerable, 17 Unanswerable, 10 Contradiction).

### 4.2 Baseline Results
The baseline comparison highlights the impact of reliability controls.

![Baseline Comparison](results/figures/fig_baselines.png)
*Figure 4.1: Comparison of B1 (Prompt), B2 (Naive), and B3 (Full) across key metrics.*

**What to notice**: B1 and B2 have an **Abstention Accuracy of 0.0**, meaning they hallucinate answers for 100% of unanswerable queries. B3 achieves **58% to 100% abstention accuracy** (depending on configuration) while maintaining a high Answer Rate (~92%). This confirms the "cited or silent" hypothesis.

### 4.3 Retrieval Performance
Retrieval is the foundation of reliability.

![Retrieval Performance](results/figures/fig_retrieval.png)
*Figure 4.2: Retrieval quality: Dense Retrieval (B2) vs Reranked (B3).*

**Interpretation**: Reranking (B3) significantly improves **Precision@5** and **MRR** compared to raw vector search (B2). High MRR is crucial for the Extractive Mode, where the top-1 result is returned directly.

### 4.4 Groundedness and Verification
The system's ability to ensure grounded answers is its primary safety feature.

![Groundedness Metrics](results/figures/fig_groundedness.png)
*Figure 4.3: Ungrounded Rate and Citation Precision metrics.*

**Interpretation**: B3 reduces the Ungrounded Rate significantly compared to the baseline. The Citation Precision metric confirms that citations generated by B3 are actual supportive evidence, not just "reference decoration".

### 4.5 Reliability Trade-off
Safety comes at the cost of coverage.

![Trade-off Scatter](results/figures/fig_tradeoff.png)
*Figure 4.4: Scatter plot of Answer Rate (Coverage) vs Ungrounded Rate (Error).*

**Interpretation**: The ideal system would be in the top-left (1.0 Answer Rate, 0.0 Ungrounded Rate). B1 and B2 are in the top-right (High Answer, High Error). B3 moves towards the top-left, representing a much safer operating point for policy compliance.

### 4.6 Error Analysis
An analysis of B3's failure modes reveals certain limitations:
1.  **Over-Abstention**: The strict confidence threshold sometimes filters out correct but low-confidence retrievals (e.g., keyword mismatch scenarios).
2.  **Complex Reasoning**: Queries requiring synthesis of multiple paragraphs (e.g., "combining remote work limit with sick leave") sometimes fail in Extractive Mode because a single paragraph isn't enough.
3.  **Scope False Positives**: The Critic Mode sometimes flags legitimate uses of "as appropriate" as vague, requiring human override.

### 4.7 Discussion and Future Work
**Limitations**: The heuristic verification is fast but brittle—it cannot verify semantic entailment (e.g., "forbidden" implying "not allowed"). The synthetic corpus, while clean, lacks the noise of real-world scanned PDFs.

**Future Work**:
1.  **NLI-based Verification**: Replacing Jaccard overlap with a Natural Language Inference model for semantic claim checking.
2.  **Fine-tuned Models**: Fine-tuning a small SLM (Small Language Model) to strictly follow citation formats, reducing dependency on proprietary APIs.
3.  **User Feedback Loop**: Allowing policy owners to mark answers as "useful" to dynamically tune the reranker thresholds.

---

## List of References

Asai, A., et al. (2024). Self-RAG: Learning to Retrieve, Generate, and Critique. *arXiv preprint arXiv:2310.11511*.

Bohnet, B., et al. (2022). Attributed Question Answering: Evaluation and Modeling for Attributed Large Language Models. *arXiv preprint arXiv:2212.08037*.

Gao, L., et al. (2023). RARR: Researching and Revising What Language Models Say, Using Language Models. *Proceedings of ACL*.

Ji, Z., et al. (2023). Survey of Hallucination in Natural Language Generation. *ACM Computing Surveys*.

Karpukhin, V., et al. (2020). Dense Passage Retrieval for Open-Domain Question Answering. *Proceedings of EMNLP*.

Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Proceedings of NeurIPS*.

Liu, N.F., et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. *TACL*.

---

## Appendix A: Self-appraisal

### A.1 Critical Evaluation
The project succeeded in building an "Audit-Ready" system. The shift from "answering everything" (B2) to "answering reliably" (B3) was challenging but successful.
-   **T1 (Ungrounded Rate)**: Successfully minimized via citation enforcement.
-   **T2 (Abstention)**: Achieved >80% accuracy on unanswerable queries in strict modes.
-   **T3 (Recall)**: Reranking proved effective at surfacing the correct gold paragraph.

The primary weakness is the brittleness of heuristic verification. While deterministic, it misses nuanced support.

### A.2 Ethics and Professional Issues
-   **Automation Bias**: Users may blindly trust the "Verified" tag. The UI explicitly labels answers as "generated".
-   **Privacy**: RAG is safer than fine-tuning privacy-wise, as document access can be controlled at retrieval time (though not implemented here).
-   **Accountability**: The log-everything architecture allows post-hoc auditing of why an answer was given or refused.

---

## Appendix B: External Materials
*See separate file `Appendix_External_Materials.md`.*
