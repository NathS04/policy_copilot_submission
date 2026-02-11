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
