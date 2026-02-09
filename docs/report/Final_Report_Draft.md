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

