# Gap Statement

## What the Field Already Does Well

The literature on retrieval-augmented generation has matured rapidly. Five capabilities are now well-established:

**1. Retrieval quality is a solved engineering problem at moderate scale.** Two-stage retrieve-and-rerank pipelines — first formalised by Nogueira and Cho (2019) and validated extensively in BEIR (Thakur et al., 2021) — achieve high recall on structured corpora. For enterprise-scale collections of fewer than 2,000 passages, cross-encoder reranking is both feasible and effective (Luan et al., 2024). Hybrid fusion strategies (Bruch et al., 2023; Cormack et al., 2009) further improve robustness by combining the complementary strengths of sparse lexical matching and dense semantic similarity.

**2. Hallucination is well-characterised.** Ji et al. (2023) and Huang et al. (2023) have established comprehensive taxonomies distinguishing intrinsic from extrinsic hallucination. The field broadly agrees that RAG reduces but does not eliminate hallucination (Lewis et al., 2020; Gao et al., 2023), and that faithfulness — fidelity to retrieved evidence — is conceptually distinct from factuality — truth in the world (Maynez et al., 2020).

**3. Citation generation is possible.** ALCE (Gao et al., 2023b), Attributed QA (Bohnet et al., 2022), and RARR (Gao et al., 2023) have demonstrated that language models can produce inline citations. The ALCE benchmark defined Citation Precision and Citation Recall as formal metrics, adopted and refined by RAGE (Zhang et al., 2024).

**4. Evaluation frameworks exist.** RAGAS (Es et al., 2023) and ARES (Saad-Falcon et al., 2023) provide decomposed evaluation along faithfulness, relevance, and context dimensions. SynCheck (Wu et al., 2024) demonstrates real-time faithfulness monitoring via decoding dynamics.

**5. The regulatory context is crystallising.** The EU AI Act (2024), NIST AI 600-1 (2024), and a growing body of governance scholarship (Mökander et al., 2023; Raji et al., 2020) are establishing expectations for AI transparency, accountability, and auditability.

## Where the Strongest Systems Still Fall Short

Despite this progress, systematic gaps remain. These gaps are not uniformly technical — they span technical, evaluative, human-factors, and governance dimensions.

### Technical Gaps

**Gap T1: Abstention is architecturally absent from most RAG systems.**
The selective prediction literature — tracing from Chow's (1970) optimal reject rule through El-Yaniv and Wiener's (2010) risk-coverage formalisation to modern LLM applications (Kamath et al., 2020; Feng et al., 2024) — has established that confidence-gated abstention can improve system reliability by concentrating outputs on high-confidence regions. Yet no production RAG system implements this as a first-class feature. Self-RAG (Asai et al., 2024) provides implicit abstention through reflection tokens but requires instruction tuning incompatible with API-based deployment. ASPIRE (Pei et al., 2023) requires fine-tuning with labelled answerability data. AbstentionBench (2025) demonstrates that reasoning fine-tuning *degrades* abstention by 24%, confirming that abstention cannot be an afterthought — it requires explicit architectural support.

**Gap T2: Contradiction handling is absent.**
Xie et al. (2024, ICLR Spotlight) categorised knowledge conflicts into context-memory, inter-context, and intra-memory types and found that all tested models struggle with implicit conflicts. Google's DRAGged framework (2024) distinguishes freshness from opinion conflicts. TCR (Chen et al., 2025) achieves +5-18 F1 on conflict detection. Yet no deployed RAG system explicitly detects and surfaces contradictions *between retrieved passages* as a user-facing feature. In policy/compliance settings, where group-level directives routinely conflict with local addenda, this gap has direct operational consequences.

**Gap T3: Deterministic verification is missing.**
Self-RAG embeds verification via learned reflection tokens; RARR applies it through additional LLM calls; SynCheck monitors decoding dynamics. All three approaches introduce non-determinism — running the same query twice may produce different verification results. For audit-critical environments, where reproducibility is a regulatory expectation (NIST AI 600-1, 2024), this non-determinism is disqualifying. Heuristic verification (e.g., Jaccard token overlap) is less expressive but produces bit-identical results across runs. The trade-off between expressiveness and determinism has not been systematically addressed in the RAG literature.

### Evaluative Gaps

**Gap E1: RAG evaluation metrics are unreliable.**
The growing critique of LLM-as-judge evaluation is severe. Zheng et al. (2024) documented verbosity, position, and self-enhancement biases. Shi et al. (2024) showed position bias is systematic across 15 judges and 150,000 instances. Ye et al. (2024, ICLR) identified 12 distinct bias types with best-case robustness of only 0.86. Wallat et al. (2024) demonstrated that 57% of citations classified as "correct" lack faithfulness — the model did not actually use them. These findings collectively undermine confidence in any evaluation that relies solely on automated metrics, including RAGAS and ARES. Human evaluation remains the gold standard, but is itself subject to the limitations documented by Sancheti and Rudinger (2024, EACL): NLI models (used in automated verification) show 23.7% out-of-domain degradation from minor surface-form variations.

**Gap E2: No evaluation framework addresses compliance-specific metrics.**
RAGAS, ARES, and RAGE focus on open-domain or general-domain QA. They do not define metrics for: abstention accuracy (proportion of correct abstain/answer decisions), contradiction recall (proportion of real contradictions detected), audit export completeness, or the risk-coverage trade-off (El-Yaniv & Wiener, 2010) that governs the precision-coverage frontier. A compliance-oriented system requires bespoke evaluation on these dimensions.

### Human-Factors Gaps

**Gap H1: Explanations do not reliably reduce overreliance.**
The trust and automation-bias literature (Parasuraman & Manzey, 2010; Lee & Moray, 1992) has long established that users over-rely on automated outputs. More recent HCI work (Bansal et al., 2021; Schemmer et al., 2023) finds that simply presenting explanations does not reliably reduce this overreliance. Buçinca et al. (2021) showed that cognitive forcing functions (requiring users to commit *before* seeing AI output) are more effective. Vasconcelos et al. (2023) refined this to show that explanations help *only when verification cost is low enough* — the user must be able to check the evidence quickly. No existing RAG system explicitly designs its evidence interface to minimise verification cost, despite this empirical finding.

### Governance Gaps

**Gap G1: Structured audit export does not exist.**
While some systems produce inspectable intermediate results (Self-RAG's reflection tokens, ARES's statistical reports), none provide a structured audit export format containing the full pipeline trace — from query through retrieval, reranking, abstention decision, generation, claim verification, and contradiction check to provider/model metadata. In compliance settings governed by the EU AI Act's transparency obligations and NIST's traceability expectations, the ability to export a complete, machine-readable audit dossier is a functional requirement. Raji et al. (2020) documented the "accountability gap" in AI development; the absence of structured export tools is a concrete manifestation of this gap.

**Gap G2: Document-level critique is a separate research stream.**
The fallacy detection literature (MAFALDA: Helwe et al., 2024; Goffredo et al., 2023; propaganda detection: Da San Martino et al., 2019) and the RAG/QA literature exist as disconnected subfields. No system integrates document-level critique — flagging normative language, unsupported claims, or argumentative fallacies — within the same interface used for evidence-grounded QA. In policy settings, the documents themselves may be defective (vague, contradictory, or rhetorically loaded), and a system that only answers questions about the documents without critiquing them provides an incomplete analysis.

## What Exact Gap Policy Copilot Addresses

Policy Copilot addresses the intersection of Gaps T1, T2, T3, E2, H1, G1, and G2 — not by solving any single problem in full generality, but by integrating six specific mechanisms within a compliance-oriented, closed-corpus RAG pipeline:

1. **Confidence-gated abstention** (T1) using cross-encoder reranker scores, externalising the abstention decision from the language model to the retrieval quality signal — architecturally distinct from ASPIRE-style self-evaluation and robust to the reasoning-degrades-abstention finding (AbstentionBench, 2025).

2. **Deterministic claim verification** (T3) via Jaccard token overlap, producing bit-identical results across runs. Less expressive than NLI-based verification but fully auditable and immune to the NLI fragility documented by Sancheti and Rudinger (2024).

3. **Contradiction detection and surfacing** (T2) using heuristic antonym/negation/numeric-mismatch detection with optional LLM escalation, presenting conflicting evidence to users rather than silently resolving it — a design choice motivated by the operational reality that policy contradictions are commonplace and that users need to see both sides.

4. **Structured audit export** (G1) in JSON and HTML with full pipeline metadata: query, retrieval results, reranking scores, abstention decision and rationale, generated answer, claim-by-claim verification, contradiction alerts, config snapshot, and provider/model metadata.

5. **L1-L6 document-level critic mode** (G2) combining heuristic detection (normative language, false dilemma, slippery slope, unsupported claims) with optional LLM-based analysis, integrated into the same UI and data pipeline as the QA system.

6. **Compliance-specific evaluation framework** (E2) with bespoke metrics: abstention accuracy, support rate, ungrounded rate, contradiction recall/precision, and component-level ablation (B1/B2/B3 baseline ladder with systematic removal of reranking, verification, and contradiction detection).

The evidence display design — citation pills linked to paragraph-level evidence, expandable evidence drawers, and the Audit Trace view — is explicitly informed by Vasconcelos et al.'s (2023) finding that explanations help when verification cost is low. By presenting quoted evidence at the point of claim, the interface minimises the effort required for a user to verify a specific statement against its source (Gap H1).

## Why This Gap Is Not Merely Incremental

The contribution is not a breakthrough in any single dimension. RAG systems already exist. Abstention mechanisms exist. Contradiction detection exists. Evaluation frameworks exist. Audit documentation approaches exist. Fallacy detection exists.

What does not exist is their *integration within a single system designed for a specific operational context* — compliance-oriented policy QA where:
- silence is better than a wrong answer,
- contradictions must be shown rather than hidden,
- every claim must link to a paragraph,
- every decision must be exportable,
- the documents themselves may be flawed, and
- the evaluation must assess reliability, not just helpfulness.

This integration is the contribution. Its significance is domain-specific, not universal: it matters in audit settings, not in open-domain chatbot design. The dissertation evaluates whether this integration works as designed, using a controlled golden set with answerable, unanswerable, and contradiction categories, component-level ablations, and honest reporting of where the system succeeds and where it fails.

## Limitations of This Gap Claim

Three caveats prevent overclaiming:

1. **Synthetic corpus.** The evaluation uses a corpus authored specifically for this project. While this enables controlled injection of test cases, results may not transfer to real-world policy documents with OCR noise, inconsistent formatting, and genuine authorship variation.

2. **Single-rater evaluation.** The human evaluation was self-administered by the author. No inter-rater agreement metrics are reportable. A genuine validation of the human-factors claims (Gap H1) would require a user study with independent participants — a limitation acknowledged in the dissertation.

3. **Heuristic verification ceiling.** Jaccard token overlap cannot detect semantic entailment or paraphrase-level support. An NLI-based verification layer (using models trained on FEVER/SciFact) would be more expressive but would sacrifice the determinism that is a design requirement. This trade-off is acknowledged as a future-work direction.
