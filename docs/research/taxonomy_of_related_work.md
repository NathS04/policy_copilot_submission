# Taxonomy of Related Work

This document organises the literature into a structured taxonomy showing major subfields, dominant methods, key limitations, unresolved tensions, and where Policy Copilot sits relative to them.

---

## 1. Retrieval-Augmented Generation

### 1.1 Intellectual Lineage

```
Memory Networks (Weston et al., 2014)
  → Open-Retrieval QA: ORQA (Lee et al., 2019), REALM (Guu et al., 2020)
    → RAG (Lewis et al., 2020) — formalised retrieval + generation coupling
      → Fusion-in-Decoder (Izacard & Grave, 2021) — multi-passage fusion
        → Self-RAG (Asai et al., 2024) — reflection tokens for self-critique
          → SEAKR (Li et al., 2025) — self-aware knowledge retrieval (ACL 2025)
```

### 1.2 Dominant Paradigms

| Paradigm | Key Works | Strengths | Limitations |
|----------|-----------|-----------|-------------|
| **Naive RAG** (retrieve → concatenate → generate) | Lewis et al. 2020 | Simple, effective, model-agnostic | No verification; faithfulness gap (Gao et al., 2023) |
| **Advanced RAG** (retrieve → rerank → generate → verify) | Barnett et al. 2024; this work | Reliability controls, error reduction | More complex pipeline; latency cost |
| **Self-reflective RAG** | Asai et al. 2024, SEAKR | End-to-end verification via reflection tokens | Requires instruction tuning; not API-compatible |
| **Post-hoc attribution** | Gao et al. 2023 (RARR), Bohnet et al. 2022 | Retrofits citations onto existing outputs | High compute cost; revision may itself hallucinate |

### 1.3 Unresolved Tension: RAG vs Long Context

Liu et al. (2024, TACL) demonstrated the "lost in the middle" phenomenon: LLMs attend poorly to information in the middle of long contexts. This has been used to argue *for* RAG (selective short-context injection). Counter-arguments from Anthropic and Google suggest that context windows > 100K tokens may eventually make retrieval unnecessary. The field has not converged. **Policy Copilot's position:** RAG provides structural auditability (explicit evidence selection) that long-context approaches cannot match, regardless of attention improvements.

### 1.4 Key Limitation of the Entire Subfield

The "faithfulness gap" (Gao et al., 2023): models frequently ignore retrieved context when it conflicts with parametric beliefs. Cuconasu et al. (2024) showed that injecting noise can paradoxically improve answers, suggesting the retrieval-generation relationship is more complex than assumed. **No RAG system has fully solved this problem.**

---

## 2. RAG Evaluation and Metrics

### 2.1 Metric Genealogy

```
N-gram overlap metrics (inadequate for faithfulness):
  BLEU (Papineni et al., 2002) — precision-oriented, translation
  ROUGE (Lin, 2004) — recall-oriented, summarisation
    ↓ "These cannot detect hallucination" (Maynez et al., 2020)

Faithfulness as a distinct concept:
  Maynez et al. (2020) — distinguished faithfulness from factuality
    → NLI-based faithfulness (Honovich et al., 2022)
      → RAGAS (Es et al., 2023) — LLM-judge decomposition
      → ARES (Saad-Falcon et al., 2023) — confidence intervals

Citation-specific metrics:
  ALCE (Gao et al., 2023b) — defined Citation Precision / Citation Recall
    → RAGE (Zhang et al., 2024) — refined citation evaluation
```

### 2.2 Dominant Methods

| Approach | Key Works | Strengths | Limitations |
|----------|-----------|-----------|-------------|
| **N-gram overlap** | BLEU, ROUGE | Fast, deterministic, reproducible | Cannot detect hallucination or semantic equivalence |
| **NLI-based** | Honovich et al. 2022, Maynez et al. 2020 | Captures semantic entailment | Fragile to paraphrase (Sancheti & Rudinger, 2024: 23.7% OOD degradation); domain-sensitive |
| **LLM-as-judge** | RAGAS, ARES, Zheng et al. 2024 | Flexible, semantic understanding | Systematic biases: position (Shi et al., 2024), verbosity, self-enhancement (Ye et al., 2024: 12 bias types); non-deterministic |
| **Deterministic heuristic** | This work (Jaccard) | Fully reproducible, auditable | Cannot capture semantic entailment or paraphrase |

### 2.3 Unresolved Tension: LLM Judges vs Determinism

The field is moving toward LLM-based evaluation (RAGAS, ARES), but systematic evidence shows these judges are unreliable:
- Shi et al. (2024): position bias across 15 judges and 150K instances
- Ye et al. (2024, ICLR): 12 distinct bias types; best models achieve only 0.86 robustness
- Wallat et al. (2024): 57% of citations lack faithfulness despite being "correct"

**Policy Copilot's position:** Uses deterministic Jaccard overlap as Tier-1 verification precisely *because* LLM judges introduce non-determinism incompatible with audit requirements. This sacrifices expressiveness for reproducibility — a deliberate, domain-motivated trade-off.

### 2.4 Key Limitation

**No gold-standard evaluation exists for RAG.** Human evaluation remains the most reliable approach but is expensive and itself subject to rater disagreement. The dissertation's single-rater evaluation is honest about this limitation.

---

## 3. Abstention and Selective Prediction

### 3.1 Intellectual Lineage

```
Optimal reject rule:
  Chow (1970) — theoretical error-reject trade-off
    → El-Yaniv & Wiener (2010) — risk-coverage formalisation; AURC metric
      → SelectiveNet (Geifman & El-Yaniv, 2019) — end-to-end learned rejection

Calibration:
  Guo et al. (2017) — modern DNNs are miscalibrated (overconfident)
    → Kamath et al. (2020) — selective QA under domain shift
      → Kadavath et al. (2022) — LLMs partially self-aware
        → Yin et al. (2023) — self-knowledge degrades OOD

LLM-era abstention:
  Pei et al. (2023, ASPIRE) — fine-tuned self-evaluation
  Feng et al. (2024, ACL Outstanding Paper) — multi-LLM collaboration
  Phung et al. (2025, TACL) — authoritative survey and taxonomy
  AbstentionBench (2025) — reasoning training degrades abstention by 24%
```

### 3.2 Field Structure

| Category | Sources | Insight |
|----------|---------|---------|
| **Foundational theory** | Chow 1970, El-Yaniv & Wiener 2010 | Optimal reject thresholds exist but require known cost ratios |
| **Calibration** | Guo et al. 2017, Kamath et al. 2020 | Raw confidence scores are unreliable; calibration is necessary |
| **LLM self-knowledge** | Kadavath et al. 2022, Yin et al. 2023 | Partial self-awareness; degrades on out-of-distribution inputs |
| **Applied abstention** | ASPIRE, Feng et al. 2024 | Fine-tuning and multi-LLM approaches improve abstention |
| **Critique/limitation** | AbstentionBench 2025, Slobodkin et al. 2024 | Reasoning training actively harms abstention; unsolved problem |

### 3.3 Unresolved Tension: Abstention vs Reasoning Quality

AbstentionBench (2025) demonstrates a fundamental tension: reasoning fine-tuning improves answer quality but degrades abstention by 24%. The very capability that makes LLMs useful actively harms their ability to know when not to answer. **Policy Copilot's position:** Sidesteps this by externalising the abstention decision to the cross-encoder reranker score rather than relying on model self-assessment. This is architecturally distinct from ASPIRE-style approaches.

### 3.4 Metric Note

"Abstention accuracy" as used in this dissertation is a bespoke metric (proportion of correct abstention/answer decisions). The established equivalents are AURC (El-Yaniv & Wiener, 2010) and Risk@Coverage. The dissertation should define this metric explicitly and position it within the risk-coverage framework.

---

## 4. Retrieval and Reranking

### 4.1 Intellectual Lineage

```
Sparse retrieval:
  TF-IDF (Salton, Wong & Yang, 1975) → BM25 (Robertson et al., 1994)

Dense retrieval:
  Siamese Networks (Bromley et al., 1993) → Sentence-BERT (Reimers & Gurevych, 2019)
    → DPR (Karpukhin et al., 2020) → ColBERT (Khattab & Zaharia, 2020)

Reranking:
  Learning to rank (Liu, 2009) → BERT reranking (Nogueira & Cho, 2019)
    → Cross-encoder vs bi-encoder trade-off (Lin et al., 2021)
      → LLM reranking: RankGPT (Sun et al., 2023, EMNLP Outstanding Paper)
        → Distillation: Rank-DistiLLM (Reddy et al., 2025, ECIR) — 173× faster than LLM

Fusion:
  Reciprocal Rank Fusion (Cormack et al., 2009)
    → Convex combination analysis (Bruch et al., 2023, ACM TOIS)
```

### 4.2 Unresolved Tension: BM25 vs Dense Retrieval

BEIR (Thakur et al., 2021) showed BM25 remains competitive in zero-shot settings; dense retrievers often fail on out-of-domain data. The debate is empirical, not resolved:

| Setting | Better Approach | Evidence |
|---------|----------------|----------|
| In-domain, well-resourced | Dense (DPR, ColBERT) | Karpukhin et al. 2020 |
| Out-of-domain / zero-shot | BM25 or hybrid | Thakur et al. 2021 (BEIR) |
| Small, structured corpus | Hybrid most robust | Bruch et al. 2023 |
| Entity-heavy queries | BM25 excels | BEIR subanalysis |
| Semantic similarity queries | Dense excels | DPR on NQ |

**Policy Copilot's position:** Uses hybrid (BM25 + dense, RRF) precisely because the corpus is small and structured, where neither approach dominates. This is empirically justified by BEIR and Bruch et al.

### 4.3 Unresolved Tension: Cross-Encoder vs LLM Reranking

RankGPT (Sun et al., 2023) showed GPT-4 outperforms cross-encoders on passage reranking benchmarks. Rank-DistiLLM (Reddy et al., 2025) showed distilled cross-encoders can match LLM-level effectiveness while being 173× faster and 24× more memory-efficient. **Policy Copilot's position:** Uses a traditional cross-encoder (ms-marco-MiniLM) because it is deterministic, fast, and does not require API access — critical properties for audit-ready operation.

---

## 5. Contradiction and Conflict Detection

### 5.1 Intellectual Lineage

```
Textual entailment:
  RTE Challenge (Dagan et al., 2005) — defined entailment/contradiction/neutral
    → SNLI (Bowman et al., 2015) — 570K training examples enabling neural NLI
      → MultiNLI (Williams et al., 2018) — multi-genre extension

Fact verification:
  FEVER (Thorne et al., 2018) — claim verification against Wikipedia
    → SciFact (Wadden et al., 2020) — scientific claim verification

Knowledge conflicts in RAG:
  Xie et al. (2024, ICLR Spotlight) — context-memory / inter-context / intra-memory taxonomy
    → TCR (Chen et al., 2025) — transparent conflict resolution (+5-18 F1)
    → DRAGged (Google, 2024) — freshness vs opinion conflict taxonomy
```

### 5.2 Key Limitation: NLI Fragility

Sancheti & Rudinger (2024, EACL): NLI models show 23.7% out-of-domain degradation from minor surface-form variations. Yang et al. (2019): models fail to generalise across benchmarks. **Implication for Policy Copilot:** NLI-based contradiction detection may be fragile to domain-specific language. The system's heuristic pre-filter (antonym/negation/numeric mismatch) partially mitigates this by catching surface-level contradictions before NLI is invoked.

### 5.3 Unresolved Tension: Explicit vs Implicit Contradictions

Xie et al. (2024) found all tested models struggle with implicit conflicts requiring reasoning (e.g., numerical contradictions: "30 days" vs "60 days"). **Policy Copilot's position:** Detects explicit contradictions (antonym pairs, direct negation) reliably but acknowledges implicit contradictions as a limitation (discussed in Section 4.7).

---

## 6. Explainability, Trust, and Human-Centred AI

### 6.1 Intellectual Lineage

```
Trust foundations:
  Muir (1994) — trust as basis for automation reliance
    → Lee & Moray (1992, 2004) — trust-calibration framework
      → Parasuraman & Manzey (2010) — automation bias synthesis

Explanation types:
  Lim & Dey (2009) — why/why-not/how explanations
    → DARPA XAI programme (2016-2021)
      → Doshi-Velez & Kim (2017) — rigorous XAI evaluation framework

Appropriate reliance:
  Bansal et al. (2021, CHI) — explanations don't always help
  Buçinca et al. (2021, CHI) — cognitive forcing functions reduce overreliance
  Vasconcelos et al. (2023, CHI) — explanations help only when verification cost is low
  Schemmer et al. (2023) — meta-analysis shows weak evidence for XAI improving decisions
```

### 6.2 Unresolved Tension: Do Explanations Actually Help?

The evidence is mixed:
- **For:** Vasconcelos et al. (2023) show explanations improve decisions *when verification cost is low*
- **Against:** Schemmer et al. (2023) meta-analysis finds weak aggregate evidence; Bansal et al. (2021) show overreliance persists with explanations
- **Nuanced:** Buçinca et al. (2021) show cognitive forcing functions (requiring users to commit before seeing AI output) reduce overreliance more than explanations alone

**Policy Copilot's position:** The citation-and-highlight design lowers verification cost by presenting evidence at the point of use, aligning with Vasconcelos et al.'s finding. The Audit Trace makes the verification process explicit rather than implicit. This is a defensible design choice grounded in the HCI literature, but the dissertation should not overclaim that explanations guarantee appropriate reliance.

---

## 7. Auditability, Governance, and Compliance

### 7.1 Intellectual Lineage

```
Accountability foundations:
  Selbst et al. (2019, FAccT) — abstraction traps in fair ML
    → Model Cards (Mitchell et al., 2019) — structured model documentation
    → Datasheets for Datasets (Gebru et al., 2021) — data documentation
      → Raji et al. (2020, AIES) — internal audit practices
        → Mökander et al. (2023) — auditing LLMs specifically

Regulatory:
  GDPR Article 22 (2016/18) — right to explanation
    → EU AI Act (2024) — risk-based classification
    → NIST AI 600-1 (2024) — GenAI risk management
```

### 7.2 Unresolved Tension: Audit-Ready vs Audit-Washing

Raji & Buolamwini (2019) and subsequent work have identified "audit-washing" — the risk that documentation and compliance features become performative rather than substantive. **Policy Copilot's position:** The system *enables* external audit by providing structured export of pipeline decisions. It does not claim to *constitute* an audit or to guarantee compliance. This distinction must be maintained in the dissertation.

---

## 8. Critic Mode and Document-Level Critique

### 8.1 Intellectual Lineage

```
Propaganda/persuasion detection:
  Da San Martino et al. (2019, EMNLP) — propaganda techniques taxonomy
    → SemEval-2020 Task 11 — propaganda detection shared task

Fallacy detection:
  Logic (Hamblin, 1970 — foundational fallacy taxonomy)
    → MAFALDA (Helwe et al., 2024, NAACL) — unified benchmark
    → Goffredo et al. (2023) — explainable three-stage framework

Claim detection:
  ClaimBuster (Hassan et al., 2017) — check-worthiness detection
    → Automated fact-checking surveys (Guo et al., 2022)
```

### 8.2 Key Limitation: LLM Fallacy Detection is Unreliable

MAFALDA (Helwe et al., 2024) showed LLMs achieve moderate zero-shot performance but remain well below supervised models on fine-grained fallacy classification. Recent work (Sourati et al., 2025) shows extreme prompt sensitivity (+0.57 F1 with structured prompts). **Policy Copilot's position:** Uses heuristic detection (regex/keyword-based L1-L6 labels) as Tier-1 precisely because heuristic outputs are deterministic and auditable, even if less expressive than LLM-based detection.

---

## 9. Research Software and Reproducibility

### 9.1 Field Structure

| Category | Sources | Finding |
|----------|---------|---------|
| **Crisis quantification** | Belz et al. 2023, Li et al. 2023 | Only 13% of NLP papers have low reproduction barriers; 46% release code |
| **Reporting standards** | Dodge et al. 2019, Pineau et al. 2021 | ML reproducibility checklists adopted but unevenly followed |
| **Regression testing** | Yan et al. 2021 | NLP model updates cause regression bugs (negative flips) |
| **Philosophical tension** | Recht 2024 vs Rolnick 2024 | Strict reproducibility vs innovation; confirmatory vs exploratory framing |

### 9.2 Unresolved Tension: Reproducibility vs Innovation

Recht (2024) argues reproducibility is the core driver of ML progress. Rolnick (2024) counters that strict reproducibility standards disadvantage applied/exploratory work. Herrmann (2024) warns against framing exploratory work as confirmatory — a relevant caution for this dissertation, which is fundamentally an exploratory systems project. **Policy Copilot's position:** Provides offline/online reproduction scripts and config snapshots, exceeding the modal standard (only 46% of NLP papers release code). The dissertation should frame its evaluation as confirmatory where metrics are pre-defined and exploratory where design choices are being investigated.

---

## 10. Legal, Social, Ethical, Professional (LSEP)

### 10.1 Key Topics

| Topic | Foundational Source | Key Finding | Relevance |
|-------|-------------------|-------------|-----------|
| **Automation bias** | Parasuraman & Manzey (2010) | Complacency and bias are overlapping attention-based phenomena | Motivates uncertainty display in UI |
| **EU AI Act** | Regulation 2024/1689 | Risk-based classification; human oversight mandates | Policy Copilot supports (not replaces) human oversight |
| **Environmental cost** | Strubell et al. (2019), Luccioni et al. (2023) | Training: 626K lbs CO2 (Transformer NAS); inference now dominates 60-90% of lifecycle emissions | RAG reduces per-query cost vs full generation |
| **Right to explanation** | Goodman & Flaxman (2017) | GDPR Article 22 implies explanation duty for automated decisions | Audit Trace provides structured explanations |
| **AI accountability** | Raji et al. (2020), Selbst et al. (2019) | Internal audit practices; abstraction traps in fairness | System enables but does not constitute audit |

### 10.2 Unresolved Tension: Automation Bias in AI-Assisted Decision Support

Wagner (2024, European Journal of Risk Regulation) analyses how the EU AI Act addresses automation bias but identifies gaps in the provider-focused approach. Jussupow et al. (2024) show non-specialists are most susceptible. **Policy Copilot's position:** The system deliberately surfaces uncertainty and abstention to counteract automation bias. The Audit Trace forces users to see the evidence chain rather than accepting a polished answer. Whether this design is effective at reducing overreliance is an empirical question that requires user study evaluation — acknowledged as future work.

---

## Where Policy Copilot Sits

Policy Copilot occupies a specific intersection that no single existing system addresses:

```
                              Abstention
                                  │
              Verification ───────┼─────── Auditability
                     │            │              │
                Contradiction     │         Structured Export
                     │            │              │
              Critic Mode ────── POLICY ─────── Evidence Display
                                COPILOT
                                  │
              Hybrid Retrieval ───┼─────── Evaluation Framework
                                  │
                           Reproducibility
```

The contribution is not a breakthrough in any single dimension but the **integration** of mechanisms that the literature has studied separately — within a compliance-oriented domain where that integration is operationally necessary.
