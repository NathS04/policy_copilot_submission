# Report-to-Research Mapping

Maps each report section to the sources that should be cited, the purpose of each citation, and the citation chain role (foundational → extending → criticising).

## Chapter 1: Introduction

| Section | Sources | Purpose | Chain Role |
|---------|---------|---------|------------|
| 1.1 Motivation: hallucination problem | Ji et al. 2023, Huang et al. 2023 | Establish hallucination taxonomy and scale-amplification | Foundational |
| 1.1 Motivation: enterprise impact | Deloitte 2024 | 38% incorrect decisions; quantify real-world risk | Practitioner evidence |
| 1.1 Motivation: regulatory context | NIST AI 600-1 2024, EU AI Act 2024, Mökander et al. 2023 | Regulatory anchor for audit-ready design | Governance |
| 1.2 Approach: RAG paradigm | Lewis et al. 2020 | Position RAG as chosen paradigm | Foundational |
| 1.2 Approach: abstention + audit | Kamath et al. 2020, Raji et al. 2020 | Position abstention and accountability as design goals | Foundational |

## Chapter 2: Background Research

| Section | Sources | Purpose | Chain Role |
|---------|---------|---------|------------|
| 2.1 RAG foundations | Lewis et al. 2020, Weston et al. 2014 (Memory Networks), Guu et al. 2020 (REALM), Izacard & Grave 2021 (FiD) | Trace RAG intellectual lineage | Foundational chain |
| 2.1 Faithfulness gap | Gao et al. 2023 (survey), Cuconasu et al. 2024, Maynez et al. 2020 | Establish faithfulness as distinct from factuality | Foundational + criticising |
| 2.1 Citation-aware RAG | Bohnet et al. 2022, Asai et al. 2024, Gao et al. 2023 (RARR), Gao et al. 2023b (ALCE), Wallat et al. 2024 | Review attribution approaches and limitations | Extending + criticising |
| 2.2 Retrieval foundations | Salton et al. 1975 (TF-IDF), Robertson et al. 1994 (BM25), Karpukhin et al. 2020 (DPR), Reimers & Gurevych 2019 (SBERT) | Trace sparse → dense retrieval lineage | Foundational chain |
| 2.2 Reranking | Nogueira & Cho 2019, Lin et al. 2021, Sun et al. 2023 (RankGPT), Reddy et al. 2025 (Rank-DistiLLM) | Two-stage pipeline justification; cross-encoder vs LLM reranking trade-off | Foundational → extending |
| 2.2 Hybrid retrieval | Cormack et al. 2009 (RRF), Bruch et al. 2023, Thakur et al. 2021 (BEIR) | Justify RRF; BM25 robustness evidence | Foundational + empirical |
| 2.2 Retrieval ceiling | Barnett et al. 2024 (Seven Failure Points) | Retrieval failure as dominant RAG failure mode | Extending |
| 2.3 Policy/Legal QA | Zhong et al. 2020, Chalkidis et al. 2020, Guha et al. 2023, Bommarito et al. 2023 | Domain context; gap in citation-verified policy QA | Contextual |
| 2.4 Abstention: theory | Chow 1970, El-Yaniv & Wiener 2010 (AURC), Guo et al. 2017 (calibration) | Theoretical foundation for reject option | Foundational chain |
| 2.4 Abstention: LLM era | Kamath et al. 2020, Kadavath et al. 2022, Pei et al. 2023, Feng et al. 2024 (ACL Outstanding), Phung et al. 2025 (TACL survey) | Selective prediction in modern QA | Extending |
| 2.4 Abstention: limits | Yin et al. 2023, Ren et al. 2023, AbstentionBench 2025 | Self-knowledge degrades OOD; reasoning harms abstention | Criticising |
| 2.5 Evaluation: metric origins | Papineni et al. 2002 (BLEU), Lin 2004 (ROUGE), Maynez et al. 2020 | Trace n-gram → faithfulness → LLM-judge paradigm shift | Metric lineage |
| 2.5 Evaluation: RAG frameworks | Es et al. 2023 (RAGAS), Saad-Falcon et al. 2023 (ARES), Zhang et al. 2024 (RAGE), Gao et al. 2023b (ALCE) | Current evaluation landscape | Extending |
| 2.5 Evaluation: LLM judge problems | Zheng et al. 2024, Shi et al. 2024, Ye et al. 2024 (CALM), Yue et al. 2023, Wallat et al. 2024 | Systematic biases in automated evaluation | Criticising |
| 2.5 Evaluation: real-time | Wu et al. 2024 (SynCheck) | Alternative faithfulness monitoring approach | Extending |
| 2.6 Contradiction: NLI foundations | Dagan et al. 2005 (RTE), Bowman et al. 2015 (SNLI) | Textual entailment task origins | Foundational chain |
| 2.6 Contradiction: fact verification | Thorne et al. 2018 (FEVER), Wadden et al. 2020 (SciFact) | Claim verification benchmarks | Foundational |
| 2.6 Contradiction: knowledge conflicts | Xie et al. 2024 (ICLR Spotlight), Chen et al. 2025 (TCR), Google 2024 (DRAGged) | Conflict taxonomy and detection methods | Extending |
| 2.6 Contradiction: NLI fragility | Sancheti & Rudinger 2024, Yang et al. 2019 | NLI models are fragile to domain shift and surface variation | Criticising |
| 2.7 Critic mode: fallacy detection | Helwe et al. 2024 (MAFALDA), Goffredo et al. 2023, Da San Martino et al. 2019 (propaganda) | Fallacy and normative language detection methods | Foundational + extending |
| 2.7 Critic mode: claim detection | Hassan et al. 2017 (ClaimBuster) | Check-worthiness detection for automated fact-checking | Foundational |
| 2.8 Gap statement | All above; comparator matrix | Synthesise what is missing; motivate Policy Copilot | Synthesis |

## Chapter 3: Methodology

| Section | Sources | Purpose | Chain Role |
|---------|---------|---------|------------|
| 3.2 Design alternatives | Liu et al. 2024 (lost in middle), Zheng et al. 2024 (LLM judges), Qu et al. 2024 (chunking) | Justify rejected alternatives with empirical evidence | Criticising |
| 3.3 Retrieval design | Karpukhin et al. 2020, Bruch et al. 2023, Cormack et al. 2009, Thakur et al. 2021 | Justify hybrid retrieval with RRF | Foundational + empirical |
| 3.4 Reranking | Nogueira & Cho 2019, Lin et al. 2021, Luan et al. 2024, Reddy et al. 2025 | Justify cross-encoder at small corpus scale | Foundational + extending |
| 3.5 Verification design | Jaccard 1912 (coefficient origin), Maynez et al. 2020 (faithfulness concept) | Justify deterministic heuristic vs NLI trade-off | Foundational |
| 3.5 Abstention design | Chow 1970, El-Yaniv & Wiener 2010, Guo et al. 2017 | Theoretical grounding for confidence-gated abstention | Foundational chain |
| 3.6 Critic mode design | Helwe et al. 2024, Goffredo et al. 2023, Da San Martino et al. 2019 | Position L1-L6 taxonomy against existing work | Extending |
| 3.7 UI/evidence design | Vasconcelos et al. 2023, Buçinca et al. 2021, Parasuraman & Manzey 2010 | Justify evidence display design based on verification-cost finding | Foundational + extending |
| 3.8 Reproducibility | Belz et al. 2023, Li et al. 2023, Dodge et al. 2019, Pineau et al. 2021 | Justify reproduction infrastructure | Foundational |

## Chapter 4: Results, Evaluation, and Discussion

| Section | Sources | Purpose | Chain Role |
|---------|---------|---------|------------|
| 4.2 Baseline comparison | Ji et al. 2023, Barnett et al. 2024 | Interpret B1 hallucination and retrieval ceiling | Contextualising |
| 4.3 Retrieval analysis | Nogueira & Cho 2019, Lin et al. 2021, Thakur et al. 2021 | Contextualise reranking impact in closed-domain setting | Contextualising |
| 4.5 Error analysis | Karpukhin et al. 2020 (vocabulary mismatch), Sancheti & Rudinger 2024 (NLI fragility) | Explain failure modes with literature evidence | Criticising |
| 4.6 Ablation | Gao et al. 2024 (RAG survey paradigms) | Position ablation findings in RAG landscape | Contextualising |
| 4.7 Limitations | Wallat et al. 2024 (correctness ≠ faithfulness), AbstentionBench 2025 (reasoning vs abstention), Sancheti & Rudinger 2024 | Bound results honestly with literature-supported limitations | Criticising |
| 4.8 LSEP: automation bias | Parasuraman & Manzey 2010, Wagner 2024, Jussupow et al. 2024 | Automation bias as primary ethical concern | Foundational + extending |
| 4.8 LSEP: right to explanation | Goodman & Flaxman 2017 (GDPR), EU AI Act 2024 | Legal basis for transparency features | Governance |
| 4.8 LSEP: environmental | Strubell et al. 2019, Luccioni et al. 2023 | Environmental cost quantification; RAG as lower-cost approach | Foundational + extending |
| 4.8 LSEP: accountability | Raji et al. 2020, Selbst et al. 2019, Mitchell et al. 2019 (Model Cards) | Accountability gap; documentation standards | Foundational |
| 4.8 LSEP: audit-washing | Raji & Buolamwini 2019 | Risk of performative compliance; honest limitations | Criticising |
| 4.9 Future work: NLI verification | Thorne et al. 2018, Wadden et al. 2020 | NLI as next step beyond Jaccard heuristic | Extending |
| 4.9 Future work: domain adaptation | Chalkidis et al. 2020 (LEGAL-BERT) | Domain-adapted embeddings for policy vocabulary | Extending |
| 4.9 Future work: user study | Vasconcelos et al. 2023, Buçinca et al. 2021 | Empirical validation of UI design claims | Future work anchor |

## Appendices

| Appendix | Sources | Purpose |
|----------|---------|---------|
| A: Self-Appraisal | None (personal reflection) | — |
| B: External Materials | Full reference list (105 sources) | — |
