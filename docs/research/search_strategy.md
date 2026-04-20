# Search Strategy

## Research Objective

Build a literature backbone for the dissertation that is "systematic and exhaustive" (Leeds excellent band), covering RAG system design, evaluation, reliability mechanisms (abstention, contradiction handling), retrieval, explainability, governance, critic-mode analysis, reproducibility, and legal/social/ethical considerations.

## Databases Searched

| Database | Type | Coverage |
|----------|------|----------|
| Google Scholar | Aggregator | Cross-venue scholarly search |
| ACM Digital Library | Publisher | HCI, IR, software engineering venues |
| IEEE Xplore | Publisher | Systems, engineering, governance |
| arXiv | Preprint | NLP, ML, AI — prioritised peer-reviewed versions where available |
| Semantic Scholar | Aggregator | Citation graph analysis, related work discovery |
| ACL Anthology | Publisher | ACL, EMNLP, NAACL, EACL proceedings |

## Search Strings Used

| Cluster | Primary Search Strings |
|---------|----------------------|
| C1: RAG Design | "retrieval-augmented generation" AND (survey OR design); "evidence-grounded question answering"; "citation-bearing generation"; "passage-level attribution" |
| C2: RAG Evaluation | "RAG evaluation framework"; "faithfulness" AND "groundedness" AND "metrics"; "citation accuracy" AND "retrieval augmented generation"; RAGAS; ARES; RAGE |
| C3: Abstention | "selective prediction" AND "language model"; "abstention" AND "question answering"; "answerability detection"; "unanswerable question" AND "retrieval" |
| C4: Retrieval + Reranking | "BM25" AND "dense retrieval" AND "comparison"; "hybrid retrieval" AND "reciprocal rank fusion"; "cross-encoder reranking" AND "passage" |
| C5: Contradiction | "contradiction detection" AND "multi-document QA"; "natural language inference" AND "retrieval"; "conflicting evidence" AND "question answering" |
| C6: Explainability / Trust | "explanation interface" AND "AI decision support"; "trust calibration" AND "AI"; "automation bias" AND "overreliance" |
| C7: Auditability / Governance | "auditability" AND "AI systems"; "NIST AI risk management"; "EU AI Act" AND "compliance"; "enterprise policy assistant" |
| C8: Critic / Bias | "normative language detection"; "argumentative fallacy detection" AND "NLP"; "unsupported claim detection"; "document-level critique" |
| C9: Reproducibility | "reproducibility" AND "NLP experiments"; "evaluation drift"; "regression testing" AND "ML" |
| C10: LSEP | "automation bias" AND "decision support"; "accountability" AND "AI knowledge systems"; "LLM carbon footprint"; "transparency" AND "explanation duty" |

## Date Range

- Primary: 2019–2025 (post-Transformer era)
- Foundational work: 2010+ where seminal (e.g., Parasuraman and Manzey, 2010)
- Standards/governance: most recent versions

## Inclusion Criteria

1. Published in a peer-reviewed venue (ACL/EMNLP/NAACL/NeurIPS/ICML/SIGIR/CHI/FAccT/AAAI) OR a substantive arXiv preprint with >10 citations
2. Directly relevant to at least one of the 10 topic clusters
3. Provides either (a) a method/system comparable to Policy Copilot's components, (b) an evaluation framework applicable to Policy Copilot, or (c) a theoretical/empirical finding that informs a design decision
4. Standards and governance documents from NIST, OECD, or EU where directly relevant

## Exclusion Criteria

1. Low-quality blog posts, SEO articles, or promotional content
2. Papers with no discernible methodology or evaluation
3. Preprints with <5 citations and no venue submission history
4. Duplicate/superseded versions (prefer the published version over the preprint)
5. Papers entirely focused on open-domain QA without relevance to closed-corpus or compliance settings

## Screening Process

1. **Title/abstract scan:** ~120 candidates identified across all clusters from database searching
2. **Initial shortlist from database search:** 48 sources selected for full review
3. **Citation chaining expansion:** backward/forward chaining identified ~55 additional candidate sources (see below)
4. **Full-text assessment:** ~115 articles assessed for eligibility after deduplication
5. **Final literature matrix:** 105 sources included after quality filtering
6. **Direct comparators:** 10 systems/papers selected for the comparator matrix
7. **Standards/governance:** 5 documents identified

## Saturation Assessment

Thematic saturation was assessed per cluster: additional searches stopped when new results predominantly returned already-identified papers or papers citing already-included work. Clusters C1 (RAG Design) and C2 (Evaluation) reached saturation earliest; C8 (Critic/Bias Detection) required the most search iterations due to the niche intersection of fallacy detection and policy document analysis.

## Additional Depth: Citation Chaining

Beyond database search, the following doctoral-standard techniques were applied:

**Backward citation chaining:** For the 15 strongest sources across all clusters, foundational works were traced backward to their intellectual origins (e.g., RAG → REALM → ORQA → Memory Networks; abstention → selective prediction → Chow 1970 reject option; NLI → SNLI → RTE Challenge).

**Forward citation chaining:** For core sources, later citing papers were examined to identify confirmations, extensions, criticisms, and replacements (e.g., Self-RAG → SEAKR 2025; RAGAS → LLM-judge bias critique literature; BM25 → BEIR zero-shot robustness finding).

**Conflict and debate analysis:** Active disagreements were systematically identified: RAG vs long context, BM25 vs dense retrieval, LLM judges vs deterministic evaluation, XAI helps vs harms, strict reproducibility vs innovation.

**Metric lineage tracing:** For all evaluation metrics used in the dissertation (Citation Precision/Recall, Faithfulness, Abstention Accuracy, Support Rate, Jaccard similarity), the originating papers were identified and the metric's strengths, limitations, and known criticisms documented.

## PRISMA-Style Flow (Broader Research Pack)

This document records the **broader research pack** flow, which counts unique title-level candidates surviving title/abstract screening. The dissertation report's Chapter 1 PRISMA (Figure 1.1) records the **stricter scholarly-review** flow, which counts raw database hits across all queries before deduplication and applies tighter inclusion criteria. Both flows are valid and complementary: the report's 38 included core studies are a strict scholarly subset, while the 105 in this matrix add contextual, practitioner, standards, and benchmark sources that support the wider methodology and LSEP discussion. The two flows are reconciled in the count hierarchy below.

```
Records identified through database searching: ~120
Records identified through citation chaining: ~55
Records after duplicate removal: ~140
Records screened (title/abstract): ~140
Records excluded at screening: ~25
Full-text articles assessed: ~115
Full-text articles excluded (irrelevance, low quality): ~10
Studies included in literature matrix: 105
  - Foundational sources: 25
  - Extending sources: 44
  - Criticising sources: 16
  - Reviews/surveys: 13
  - Benchmarks/datasets: 8
  - Standards/regulations: 2
Direct comparator systems: 10
```

*Note: Role categories are non-exclusive; some sources serve multiple roles (e.g., a review that also criticises, or a benchmark that is also foundational). The six role counts therefore sum to more than 105.*

## Count Hierarchy (Single Source of Truth)

| Tier | Count | Definition | Where Reported |
|------|-------|------------|----------------|
| Raw database hits (cross-database, with duplicates) | 584 | All matches across Google Scholar / ACM / IEEE / arXiv before deduplication | Report §1.3 PRISMA |
| Records after deduplication (report flow) | 472 | Unique records screened by title/abstract | Report §1.3 PRISMA |
| Full-text assessed (report flow) | 154 | Records passing title/abstract screening | Report §1.3 PRISMA |
| **Core peer-reviewed studies (strict scholarly review)** | **38** | Pass strict scholarly inclusion criteria; form the literature review backbone | Report Chapter 1 |
| Unique title-level candidates (matrix flow) | ~120 | Cross-cluster, deduplicated at title-screening step | This file (above) |
| Citation-chain additions | ~55 | Backward + forward chaining beyond database search | This file |
| **All sources in research pack matrix** | **105** | 38 core + 67 additional contextual/practitioner/standards sources | `literature_matrix.md` |
| Direct comparator systems | 10 | Subset evaluated in Table 1.1 | `comparator_matrix.md` / Appendix B.8 |

The 584 → 38 figures and the 120 → 105 figures are not contradictory: they describe two different flows over overlapping but distinct corpora. The strict 38 are the formal literature review; the broader 105 contextualise it.

## Saturation Assessment

Saturation was assessed per cluster:
- **Reached:** C1 (RAG design), C2 (evaluation), C3 (abstention), C4 (retrieval), C6 (trust/HCI), C7 (governance), C9 (reproducibility), C10 (LSEP)
- **Near saturation:** C5 (contradiction — active 2024-2025 frontier), C8 (critic/bias — niche intersection of fallacy detection and policy analysis)

For clusters at near-saturation, new sources predominantly report incremental extensions of already-identified frameworks (e.g., new conflict resolution techniques building on Xie et al.'s taxonomy).
