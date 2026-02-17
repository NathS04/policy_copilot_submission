# Literature Matrix

## Source Quality Legend

- **Venue Tier:** T1 = top-tier peer-reviewed (ACL, EMNLP, NeurIPS, ICML, ICLR, SIGIR, TACL, CHI, FAccT, JMLR, IEEE T-IT, ACM Computing Surveys); T2 = strong venue (NAACL, AAAI, CIKM, EACL, ECIR, ACL Findings, workshops, established journals); T3 = arXiv-only or practitioner source
- **Source Type:** E = empirical, C = conceptual/theoretical, S = system/implementation, R = review/survey, B = benchmark/dataset, St = standard/regulation, P = practitioner
- **Relevance:** Direct = core to Policy Copilot's design; Supporting = informs a design choice; Contextual = provides domain or theoretical background

## Cluster C1 — RAG System Design

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 1 | Lewis et al. (RAG) | NeurIPS (T1) | 2020 | S | Direct | **Foundational** | Formalised retrieval + generation coupling for knowledge-intensive tasks |
| 2 | Ji et al. (hallucination survey) | ACM Comp. Surveys (T1) | 2023 | R | Direct | Foundational | Intrinsic/extrinsic hallucination taxonomy motivating verification |
| 3 | Huang et al. (LLM hallucination) | arXiv (T3) | 2023 | R | Direct | Foundational | Scale amplifies hallucination confidence; motivates external controls |
| 4 | Gao et al. (RAG survey) | arXiv (T3) | 2024 | R | Supporting | Extending Lewis | Categorises Naive/Advanced/Modular RAG paradigms |
| 5 | Bohnet et al. (Attributed QA) | arXiv (T3) | 2022 | S | Direct | Extending | Citation correctness ≠ faithfulness; motivates verification |
| 6 | Asai et al. (Self-RAG) | ICLR (T1) | 2024 | S | Direct | Extending Lewis | Reflection tokens; requires instruction tuning; architecturally inappropriate for API systems |
| 7 | Gao et al. (RARR) | ACL (T1) | 2023 | S | Direct | Extending Lewis | Post-hoc revision; high compute cost; revision may hallucinate |
| 8 | Brown et al. (GPT-3) | NeurIPS (T1) | 2020 | E | Supporting | Foundational | Few-shot prompting efficacy for format adherence |
| 9 | Weston et al. (Memory Networks) | arXiv/ICLR (T1) | 2014 | S | Contextual | **Pre-RAG foundational** | External memory for QA; intellectual ancestor of RAG |
| 10 | Guu et al. (REALM) | ICML (T1) | 2020 | S | Contextual | Pre-RAG | Retrieval as latent variable during pretraining |
| 11 | Izacard & Grave (FiD) | EACL (T2) | 2021 | S | Supporting | Extending Lewis | Multi-passage fusion; encoder processes passages independently |
| 12 | Cuconasu et al. (Power of Noise) | SIGIR (T1) | 2024 | E | Supporting | Criticising naive RAG | Noise paradoxically improves; retrieval-generation relationship is complex |
| 101 | Li et al. (SEAKR) | arXiv (T3) | 2025 | S | Direct | Extending Self-RAG | Replaces reflection tokens with uncertainty-aware retrieval from LLM internal states; avoids instruction tuning |

**Saturation assessment:** Reached. The RAG design space is well-mapped. New work is primarily system engineering or domain-specific application.

## Cluster C2 — RAG Evaluation / Faithfulness / Groundedness

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 13 | Es et al. (RAGAS) | arXiv (T3) | 2023 | S,B | Direct | Foundational (modern) | Decomposed RAG eval: Faithfulness, Answer Relevance, Context Relevance |
| 14 | Saad-Falcon et al. (ARES) | arXiv (T3) | 2023 | S | Direct | Extending RAGAS | Adds confidence intervals and statistical significance |
| 15 | Zhang et al. (RAGE) | arXiv (T3) | 2024 | S,B | Direct | Extending ALCE | Refined Citation-Precision and Citation-Recall |
| 16 | Zheng et al. (LLM judges) | NeurIPS (T1) | 2024 | E | Direct | Criticising LLM eval | Systematic biases: verbosity, position, self-enhancement |
| 17 | Wallat et al. (correctness ≠ faithfulness) | arXiv (T3) | 2024 | E | Direct | Criticising citation eval | 57% of citations lack faithfulness despite being "correct" |
| 18 | Yue et al. (judge circularity) | arXiv (T3) | 2023 | E | Supporting | Criticising LLM eval | LLM judges share biases with generators |
| 19 | Chen et al. (RAG benchmarking) | AAAI (T2) | 2024 | B | Supporting | Extending | LLM performance in RAG settings |
| 20 | Papineni et al. (BLEU) | ACL (T1) | 2002 | C,S | Contextual | **Metric origin** | N-gram precision; cannot detect hallucination |
| 21 | Lin (ROUGE) | ACL Workshop (T2) | 2004 | C,S | Contextual | **Metric origin** | Recall-oriented; same limitations as BLEU for RAG |
| 22 | Maynez et al. (faithfulness origin) | ACL (T1) | 2020 | E | Direct | **Foundational** | Distinguished faithfulness from factuality; showed ROUGE fails for hallucination |
| 23 | Gao et al. (ALCE benchmark) | EMNLP (T1) | 2023 | B | Direct | **Metric origin** | Defined Citation Precision / Citation Recall as formal metrics |
| 24 | Shi et al. (position bias) | IJCNLP-AACL (T2) | 2024 | E | Supporting | Criticising LLM eval | Position bias systematic across 15 judges, 150K instances |
| 25 | Ye et al. (CALM) | ICLR (T1) | 2024 | E | Supporting | Criticising LLM eval | 12 bias types; best models only 0.86 robustness |
| 26 | Wu et al. (SynCheck) | EMNLP (T1) | 2024 | S | Supporting | Extending | Real-time faithfulness monitoring via decoding dynamics; >0.85 AUROC |
| 102 | Honovich et al. (TRUE) | NAACL (T1) | 2022 | E | Direct | Foundational | NLI-based faithfulness evaluation; showed NLI transfer to factual consistency checking |

**Saturation assessment:** Reached for evaluation frameworks. Active frontier in LLM-judge criticism — new critique papers appear frequently but converge on the same conclusion (judges are unreliable).

## Cluster C3 — Abstention / Selective QA

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 27 | Chow (reject option) | IEEE T-IT (T1) | 1970 | C | Contextual | **Theoretical origin** | Optimal error-reject trade-off; no rule beats Bayes with rejection |
| 28 | El-Yaniv & Wiener (risk-coverage) | JMLR (T1) | 2010 | C | Contextual | **Theoretical foundation** | Formalised AURC; optimality conditions for selective classifiers |
| 29 | Guo et al. (calibration) | ICML (T1) | 2017 | E | Supporting | Foundational | Modern DNNs systematically miscalibrated; temperature scaling |
| 30 | Kamath et al. (selective QA) | EMNLP (T1) | 2020 | E | Direct | Extending Chow/El-Yaniv | Calibrated confidence for selective QA under domain shift |
| 31 | Kadavath et al. (LLM self-knowledge) | arXiv (T3) | 2022 | E | Direct | Extending | Larger models better calibrated but substantial domain variation |
| 32 | Pei et al. (ASPIRE) | arXiv (T3) | 2023 | S | Direct | Extending | Fine-tuned self-evaluation scores; requires labelled data |
| 33 | Yin et al. (LLM limits) | arXiv (T3) | 2023 | E | Direct | Criticising | Self-knowledge degrades on OOD queries |
| 34 | Ren et al. (RAG factual boundary) | arXiv (T3) | 2023 | E | Direct | Extending | RAG improves but doesn't eliminate factual boundary |
| 35 | Feng et al. (ACL Outstanding) | ACL (T1) | 2024 | S | Direct | Extending | Multi-LLM collaboration for abstention; highest-impact recent paper |
| 36 | Phung et al. (abstention survey) | TACL (T1) | 2025 | R | Direct | Extending | Authoritative peer-reviewed taxonomy of LLM abstention |
| 37 | Geifman & El-Yaniv (SelectiveNet) | ICML (T1) | 2019 | S | Supporting | Extending El-Yaniv | Joint training outperforms post-hoc thresholding |
| 38 | AbstentionBench | arXiv (T3) | 2025 | B | Supporting | **Criticising** | Reasoning fine-tuning degrades abstention by 24% |
| 39 | Slobodkin et al. (abstention survey) | arXiv (T3) | 2024 | R | Supporting | Extending | Three-dimensional taxonomy: query/model/value-level abstention |

**Saturation assessment:** Reached. Core theory stable since El-Yaniv & Wiener 2010. LLM-era work is actively debating whether models can reliably self-assess — AbstentionBench 2025 is the latest (negative) data point.

## Cluster C4 — Retrieval + Reranking

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 40 | Robertson et al. (BM25) | TREC (T2) | 1994 | C,S | Direct | **Foundational** | Probabilistic term-weighting; remains competitive 30 years later |
| 41 | Karpukhin et al. (DPR) | EMNLP (T1) | 2020 | S | Direct | Foundational | Dense passage retrieval via bi-encoders |
| 42 | Johnson, Douze & Jégou (FAISS) | IEEE Trans. Big Data (T1) | 2021 | S | Direct | Infrastructure | Billion-scale approximate nearest-neighbour search |
| 43 | Nogueira & Cho (BERT reranking) | arXiv (T3) | 2019 | S | Direct | **Foundational** | Cross-encoder reranking; 27% relative improvement on MS MARCO |
| 44 | Lin et al. (transformers for ranking) | Synthesis Lectures (T2) | 2021 | R | Direct | Extending | Cross-encoders consistently outperform bi-encoders in precision |
| 45 | Thakur et al. (BEIR) | NeurIPS (T1) | 2021 | B | Direct | **Foundational** (benchmark) | BM25 remains robust zero-shot; dense retrievers fail OOD |
| 46 | Bruch et al. (fusion functions) | ACM TOIS (T1) | 2023 | E | Direct | Extending | Convex combination generally outperforms RRF |
| 47 | Barnett et al. (failure points) | CAIN (T2) | 2024 | E | Direct | Extending | Retrieval failure is the dominant RAG failure mode |
| 48 | Liu et al. (lost in the middle) | TACL (T1) | 2024 | E | Supporting | Criticising long context | Information in middle of long contexts poorly attended |
| 49 | Luan et al. (latency-precision) | arXiv (T3) | 2024 | E | Supporting | Extending | Two-stage reranking feasible at small corpus scale |
| 50 | Qu, Bao & Tu (chunking) | arXiv (T3) | 2024 | E | Supporting | Extending | Paragraph chunking competitive with semantic chunking |
| 51 | Reimers & Gurevych (Sentence-BERT) | EMNLP (T1) | 2019 | S | Supporting | Foundational | Siamese BERT for sentence embeddings; enables bi-encoder retrieval |
| 52 | Khattab & Zaharia (ColBERT) | SIGIR (T1) | 2020 | S | Contextual | Extending DPR | Late interaction; trade-off between bi-encoder speed and cross-encoder quality |
| 53 | Sun et al. (RankGPT) | EMNLP Outstanding (T1) | 2023 | S | Contextual | Extending reranking | LLM reranking outperforms cross-encoders on benchmarks |
| 54 | Reddy et al. (Rank-DistiLLM) | ECIR (T2) | 2025 | S | Supporting | Extending | Distilled cross-encoders match LLM reranking at 173× lower cost |
| 55 | Cormack et al. (RRF) | SIGIR (T1) | 2009 | C | Direct | **Foundational** | Reciprocal Rank Fusion for combining ranked lists |
| 56 | Salton, Wong & Yang (TF-IDF) | CACM (T1) | 1975 | C | Contextual | **Foundational** (historical) | Vector space model; intellectual ancestor of all IR |

**Saturation assessment:** Reached. The retrieve-and-rerank two-stage paradigm is well-established. Active frontier is LLM-based reranking and efficiency (distillation).

## Cluster C5 — Contradiction / Conflict Handling

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 57 | Dagan et al. (RTE) | MLCW/Springer (T2) | 2005 | C,B | Contextual | **Foundational** | Defined entailment/contradiction/neutral classification |
| 58 | Bowman et al. (SNLI) | EMNLP (T1) | 2015 | B | Contextual | **Foundational** | 570K examples; enabled neural NLI; all modern NLI models trace here |
| 59 | Thorne et al. (FEVER) | NAACL (T1) | 2018 | B | Direct | Foundational | Fact verification benchmark; NLI for claim checking |
| 60 | Wadden et al. (SciFact) | EMNLP (T1) | 2020 | B | Supporting | Extending FEVER | Scientific claim verification via NLI |
| 61 | Xie et al. (knowledge conflicts) | ICLR Spotlight (T1) | 2024 | R | Direct | Extending | Context-memory / inter-context / intra-memory conflict taxonomy |
| 62 | Sancheti & Rudinger (NLI fragility) | EACL (T1) | 2024 | E | Direct | **Criticising NLI** | 23.7% OOD degradation from surface-form variation |
| 63 | Yang et al. (NLI generalisation) | EMNLP Workshop (T2) | 2019 | E | Supporting | Criticising NLI | Models fail to generalise across benchmarks |
| 64 | Chen et al. (TCR) | arXiv (T3) | 2025 | S | Supporting | Extending Xie | Transparent conflict resolution; +5-18 F1 |
| 65 | Google (DRAGged) | Google Research (T1) | 2024 | S | Supporting | Extending | Freshness vs opinion conflict taxonomy for RAG |

**Saturation assessment:** Near saturation. Contradiction detection in RAG is a nascent subfield with rapid growth (2024-2025). The core taxonomy (Xie et al.) is established; implementation approaches are still diverging.

## Cluster C6 — Explainability / Trust / Human-Centred AI

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 66 | Parasuraman & Manzey (automation bias) | Human Factors (T1) | 2010 | R | Direct | **Foundational** | Complacency and bias are overlapping attention-based phenomena |
| 67 | Lee & Moray (trust in automation) | Ergonomics (T1) | 1992 | E | Contextual | **Foundational** | Trust-calibration framework for automated systems |
| 68 | Doshi-Velez & Kim (XAI evaluation) | arXiv (T3) | 2017 | C | Supporting | Foundational | Framework for rigorous evaluation of interpretability |
| 69 | Buçinca et al. (cognitive forcing) | CHI (T1) | 2021 | E | Supporting | Extending | Cognitive forcing functions reduce overreliance more than explanations |
| 70 | Bansal et al. (overreliance) | CHI (T1) | 2021 | E | Supporting | **Criticising XAI** | Explanations don't reliably reduce overreliance |
| 71 | Vasconcelos et al. (verification cost) | CHI (T1) | 2023 | E | Direct | Extending | Explanations help only when verification cost is low enough |
| 72 | Schemmer et al. (XAI meta-analysis) | arXiv (T3) | 2023 | R | Supporting | **Criticising XAI** | Weak aggregate evidence for XAI improving decisions |

**Saturation assessment:** Reached. The trust/automation-bias lineage is mature (30+ years). The "do explanations help?" debate continues but the core positions are established.

## Cluster C7 — Auditability / Governance / Compliance

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 73 | Deloitte AI Institute | Industry (P) | 2024 | P | Direct | Contextual | 38% incorrect decisions from AI; motivates audit-ready design |
| 74 | NIST AI 600-1 | Standard (St) | 2024 | St | Direct | Contextual | GenAI risk management framework; regulatory anchor |
| 75 | Mökander et al. (auditing LLMs) | Digital Society (T2) | 2023 | C | Direct | Extending | Governance framework for LLM auditability |
| 76 | Raji et al. (accountability gap) | AIES (T2) | 2020 | C | Supporting | Foundational | Internal audit practices for AI systems |
| 77 | Mitchell et al. (Model Cards) | FAccT (T1) | 2019 | C | Supporting | Foundational | Structured model documentation standard |
| 78 | Gebru et al. (Datasheets) | CACM (T1) | 2021 | C | Supporting | Foundational | Dataset documentation standard |
| 79 | Selbst et al. (abstraction traps) | FAccT (T1) | 2019 | C | Contextual | **Foundational** | Five traps in fair ML; warns against decontextualised audit |
| 80 | Chari et al. (KG for accountability) | AI and Ethics (T2) | 2023 | S | Contextual | Extending | Knowledge graph ontologies for audit information |
| 81 | Zhong et al. (legal NLP survey) | arXiv (T3) | 2020 | R | Supporting | Contextual | NLP applications in legal systems |
| 82 | Chalkidis et al. (LEGAL-BERT) | EMNLP Findings (T2) | 2020 | S | Supporting | Extending | Domain-specific legal pretraining |
| 83 | Guha et al. (LegalBench) | NeurIPS (T1) | 2023 | B | Supporting | Extending | GPT-4 struggles with multi-step legal reasoning |
| 84 | Katz et al. (GPT-4 Bar Exam) | arXiv (T3) | 2024 | E | Contextual | Extending | LLM performance on bar examination |
| 85 | Bommarito et al. (legal NLP gap) | arXiv (T3) | 2023 | R | Supporting | Extending | Gap in citation-verified legal QA |
| 103 | Raji & Buolamwini (audit-washing) | FAccT (T1) | 2019 | C | Direct | **Criticising** | External vs internal audit; AI audit can serve as performative compliance without substantive accountability |
| 104 | Mökander et al. (checkbox AI ethics) | AI and Ethics (T2) | 2024 | R | Supporting | **Criticising** | Documents ethics-washing, low adoption rates for ethical AI; warns against conflating documentation with compliance |

**Saturation assessment:** Reached for governance/audit theory. The regulatory landscape (EU AI Act, NIST) is evolving but current sources are up-to-date.

## Cluster C8 — Critic Mode / Bias Detection

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 86 | Helwe et al. (MAFALDA) | NAACL (T1) | 2024 | B | Direct | Foundational (modern) | Unified fallacy benchmark; LLMs moderate zero-shot, below supervised |
| 87 | Goffredo et al. (explainable fallacies) | KBS (T2) | 2023 | S | Direct | Extending | Three-stage detection-classification-explanation framework |
| 88 | Da San Martino et al. (propaganda) | EMNLP (T1) | 2019 | B | Supporting | **Foundational** | Propaganda techniques taxonomy; 18-class fine-grained detection |
| 89 | Hassan et al. (ClaimBuster) | VLDB (T1) | 2017 | S | Supporting | Foundational | Check-worthiness detection; automated fact-checking pipeline |

**Saturation assessment:** Near saturation for detection methods. The intersection of fallacy detection with policy document analysis is niche — Policy Copilot's L1-L6 taxonomy is domain-specific and not directly benchmarked against existing datasets.

## Cluster C9 — Research Software / Reproducibility

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 90 | Belz et al. (ReproNLP) | HumEval Workshop (T2) | 2023 | E | Direct | Extending | Only 13% of NLP papers have low reproduction barriers |
| 91 | Li et al. (reproducibility checklist) | ACL Findings (T2) | 2023 | E | Supporting | Extending | 46% of submissions open-source code; reproducibility checklists help |
| 92 | Dodge et al. (show your work) | EMNLP (T1) | 2019 | C | Supporting | Foundational | Reporting validation as function of computation budget |
| 93 | Yan et al. (regression bugs) | ACL (T1) | 2021 | E | Supporting | Extending | NLP model updates cause negative flips; distillation mitigates |
| 94 | Pineau et al. (ML reproducibility) | JMLR (T1) | 2021 | C | Supporting | Foundational | ML reproducibility checklist adopted at NeurIPS/ICML |
| 105 | Rolnick et al. (application-driven ML) | ICML (T1) | 2024 | C | Supporting | **Criticising** | Strict reproducibility standards may disadvantage applied work; strongest counterargument to Policy Copilot's reproducibility emphasis |

**Saturation assessment:** Reached. The reproducibility crisis is well-documented; the main debate is standards vs flexibility.

## Cluster C10 — Legal / Social / Ethical / Professional

| # | Citation | Venue (Tier) | Year | Type | Relevance | Role in Citation Chain | Key Finding |
|---|----------|-------------|------|------|-----------|----------------------|-------------|
| 95 | Strubell et al. (NLP energy) | ACL (T1) | 2019 | E | Direct | **Foundational** | Quantified CO2 of training; up to 626K lbs for architecture search |
| 96 | Luccioni et al. (BLOOM carbon) | JMLR (T1) | 2023 | E | Direct | Extending Strubell | First lifecycle LLM carbon analysis; 50.5 tonnes CO2eq |
| 97 | Wagner (automation bias EU AI Act) | Eur. J. Risk Reg. (T2) | 2024 | C | Direct | Extending | Gaps in EU AI Act's provider-focused approach to bias |
| 98 | Goodman & Flaxman (right to explanation) | AI and Society (T2) | 2017 | C | Supporting | Foundational | GDPR implies explanation duty for automated decisions |
| 99 | Jussupow et al. (automation bias empirical) | AMIA (T2) | 2024 | E | Supporting | Extending | Non-specialists most susceptible to automation bias |
| 100 | Jaccard (coefficient origin) | New Phytologist (T1) | 1912 | C | Contextual | **Historical** | Set-theoretic similarity coefficient origin |

**Saturation assessment:** Reached. Environmental cost is actively updated but the core framework (training vs inference, carbon vs water) is established.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total sources in matrix | 105 |
| Tier 1 venues | 59 |
| Tier 2 venues | 27 |
| Tier 3 / practitioner | 19 |
| Sources already cited in report | 37 |
| New sources from research sweep | 68 |
| Foundational sources | 25 |
| Extending sources | 44 |
| Criticising sources | 16 |
| Reviews/surveys | 13 |
| Benchmarks/datasets | 8 |
| Standards/regulations | 2 |

## Cluster Coverage

| Cluster | Sources | Saturation |
|---------|---------|------------|
| C1: RAG Design | 13 | Reached |
| C2: RAG Evaluation | 15 | Reached |
| C3: Abstention | 13 | Reached |
| C4: Retrieval + Reranking | 17 | Reached |
| C5: Contradiction | 9 | Near (active frontier) |
| C6: Explainability/Trust | 7 | Reached |
| C7: Governance/Compliance | 15 | Reached |
| C8: Critic/Bias | 4 | Near (niche intersection) |
| C9: Reproducibility | 6 | Reached |
| C10: LSEP | 6 | Reached |
