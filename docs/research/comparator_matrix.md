# Comparator Matrix

Compares Policy Copilot against 10 closely relevant systems/papers on key design axes, informed by backward/forward citation chaining.

## Comparison Axes

- **Retrieval:** What retrieval strategy is used?
- **Reranking:** Is cross-encoder or other reranking applied?
- **Citation/Evidence:** How are citations linked to evidence?
- **Abstention:** Does the system refuse to answer when evidence is insufficient?
- **Contradiction:** Is conflicting evidence detected and surfaced?
- **Verification:** How is answer faithfulness verified?
- **Human Eval:** Was a human evaluation conducted?
- **Auditability/Export:** Can pipeline decisions be inspected and exported?
- **Critic/Analysis:** Does the system provide document-level critique beyond QA?
- **Reproducibility:** Is the system reproducible from published artifacts?

## Matrix

| System | Retrieval | Reranking | Citation | Abstention | Contradiction | Verification | Human Eval | Audit Export | Critic | Repro |
|--------|-----------|-----------|----------|------------|---------------|-------------|------------|------------|--------|-------|
| **Policy Copilot** | Hybrid RRF (BM25+dense) | Cross-encoder | Per-claim paragraph-level, Jaccard-verified | Confidence-gated (reranker score) | Heuristic + optional LLM | Deterministic Jaccard | Single-rater (20 queries) | JSON/HTML with full metadata | L1-L6 heuristic + LLM | Offline/online scripts, config snapshots |
| **Self-RAG** (Asai+, ICLR 2024) | Learned timing | None | Reflection tokens | Implicit [IsSupported] | Not addressed | Reflection tokens (non-deterministic) | Automatic only | Tokens inspectable | None | Code; requires instruction tuning |
| **RARR** (Gao+, ACL 2023) | Multi-step web | None | Post-hoc editing | None | None | LLM revision (non-deterministic) | Human attribution | Attribution rationales | None | Code released |
| **ALCE** (Gao+, EMNLP 2023) | Document | None | Inline generation | None | None | Citation P/R metrics | Human + automatic | Citation metrics | None | Benchmark released |
| **RAGAS** (Es+, 2023) | N/A (eval framework) | N/A | Faithfulness decomposition | None | None | LLM-as-judge | LLM-based | Metric decomposition | None | Code released |
| **ARES** (Saad-Falcon+, 2023) | N/A (eval framework) | N/A | Citation quality metrics | None | None | LLM-as-judge + CIs | Confidence intervals | Statistical reporting | None | Code released |
| **SynCheck** (Wu+, EMNLP 2024) | Standard RAG | None | N/A | None | None | Decoding dynamics (>0.85 AUROC) | Automatic | Real-time monitoring | None | Code released |
| **ASPIRE** (Pei+, 2023) | Standard | None | N/A | Fine-tuned self-eval | None | Self-evaluation scores | Automatic | Confidence scores | None | Code released |
| **TCR** (Chen+, 2025) | Standard RAG | None | N/A | None | Transparent resolution (+5-18 F1) | None | Automatic | Conflict rationales | None | Partial |
| **DRAGged** (Google, 2024) | Standard RAG | None | N/A | None | Freshness vs opinion taxonomy | None | Automatic | Conflict taxonomy | None | N/A |
| **Seven Failure Points** (Barnett+, CAIN 2024) | Analysis of multiple | Discusses impact | Identifies failure modes | Identifies gap | Discusses conflicts | N/A (analysis paper) | Production cases | Failure taxonomy | None | N/A |

## Key Observations (Doctoral-Depth)

### 1. Abstention remains architecturally rare

Only ASPIRE and Policy Copilot implement explicit abstention. Self-RAG's [IsSupported] tokens provide implicit abstention but require instruction tuning. The fundamental tension identified by AbstentionBench (2025) — that reasoning fine-tuning degrades abstention by 24% — explains why abstention is architecturally rare: optimising for answer quality and optimising for knowing-when-not-to-answer are competing objectives. Policy Copilot sidesteps this by externalising abstention to the cross-encoder reranker score.

### 2. Contradiction handling is an active frontier with no mature solution

Only TCR and DRAGged explicitly address contradictions, and both are 2024-2025 publications. Xie et al. (2024) showed all models struggle with implicit conflicts. Policy Copilot's heuristic approach (antonym/negation/numeric mismatch) handles explicit contradictions reliably but misses implicit ones — a limitation shared with all current systems.

### 3. Verification approaches reflect a fundamental expressiveness-determinism trade-off

| Approach | System | Deterministic? | Expressive? | Audit-safe? |
|----------|--------|---------------|-------------|-------------|
| Reflection tokens | Self-RAG | No (model stochasticity) | High | No |
| LLM revision | RARR | No (additional LLM call) | High | No |
| Decoding dynamics | SynCheck | Partially (threshold-dependent) | Medium | Partially |
| LLM-as-judge | RAGAS, ARES | No (12 bias types, Ye et al. 2024) | High | No |
| Heuristic (Jaccard) | Policy Copilot | Yes (bit-identical) | Low | Yes |

No system resolves this trade-off fully. Policy Copilot's choice of deterministic verification is domain-motivated (audit requirements) rather than technically superior.

### 4. Structured audit export is genuinely absent

No comparator provides a structured, machine-readable export of the full pipeline trace. This is not a minor engineering gap — it reflects the field's optimisation for *performance* (answer quality) over *inspectability* (audit trail). In compliance settings governed by the EU AI Act and NIST AI 600-1, this absence is operationally significant.

### 5. Document-level critique occupies a distinct niche

The fallacy detection literature (MAFALDA, Goffredo et al.) and the RAG/QA literature exist as disconnected subfields. Policy Copilot's critic mode integrates normative language detection into the QA interface — a combination not found in any comparator. However, the heuristic approach is less expressive than MAFALDA's supervised models, and MAFALDA's finding that LLMs achieve moderate zero-shot performance suggests LLM-based critic detection may eventually supersede heuristics.

### 6. Reproducibility is better-than-modal but not exceptional

Policy Copilot's reproduction infrastructure (offline/online scripts, config snapshots, evaluator instructions) exceeds the 46% code-release rate reported by Li et al. (2023). However, it does not meet the highest reproducibility standards (e.g., containerised environments, pre-built Docker images, one-command full reproduction). This is acknowledged as a practical constraint.

## Where Policy Copilot Sits in the Comparator Space

Policy Copilot is not the strongest system on any single axis. It does not match Self-RAG's end-to-end integration, RAGAS's evaluation breadth, or SynCheck's real-time monitoring sophistication. Its contribution is the *combination* of abstention + deterministic verification + contradiction surfacing + audit export + critic mode within a single compliance-oriented system — a combination no comparator achieves.
