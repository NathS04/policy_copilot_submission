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
