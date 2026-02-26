# Citation Chaining & Conflict Analysis — Clusters 1 & 4

## Purpose
Doctoral-level backward/forward citation chaining and conflict identification for the two core technical clusters of the dissertation. Each source is assessed for relevance, quality, and venue tier.

**Relevance grading key:** A* = directly validates a core design choice; A = strongly relevant to dissertation scope; A- = relevant with minor caveats; B+ = relevant supporting evidence; B = tangentially relevant. Grades are the author's assessment of direct relevance to this dissertation, not venue quality.

---

## CLUSTER 1 — RAG SYSTEM DESIGN

### Seed Papers
- Lewis et al. 2020 (RAG) — NeurIPS
- Asai et al. 2024 (Self-RAG) — ICLR
- Gao et al. 2023 (RARR) — ACL
- Bohnet et al. 2022 (Attributed QA) — arXiv

---

### 1.1 BACKWARD CHAINING (Foundational Works)

#### Source 1: Guu et al. 2020 — REALM
- **Full citation:** Guu, K., Lee, K., Tung, Z., Pasupat, P. and Chang, M.-W. (2020) 'REALM: Retrieval-Augmented Language Model Pre-Training', *Proceedings of the 37th International Conference on Machine Learning (ICML)*, PMLR 119, pp. 3929–3938.
- **URL:** https://proceedings.mlr.press/v119/guu20a.html | arXiv:2002.08909
- **Relationship:** **Foundational** — direct precursor to Lewis et al. 2020 RAG. REALM was the first to demonstrate end-to-end pre-training of a knowledge retriever jointly with a language model, backpropagating through a retrieval step over millions of documents.
- **Assessment:** Indispensable for establishing the intellectual lineage of RAG. REALM showed that learned retrieval could be integrated into LM pre-training; Lewis et al. extended this to generative seq2seq tasks. Without REALM, the conceptual leap to RAG is unexplained.
- **Venue tier:** **Tier-1** (ICML)

#### Source 2: Lee, Chang & Toutanova 2019 — ORQA
- **Full citation:** Lee, K., Chang, M.-W. and Toutanova, K. (2019) 'Latent Retrieval for Weakly Supervised Open Domain Question Answering', *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics (ACL)*, Florence, pp. 6086–6096. DOI: 10.18653/v1/P19-1612.
- **URL:** https://aclanthology.org/P19-1612/
- **Relationship:** **Foundational** — demonstrated that dense retrieval could outperform BM25 for open-domain QA using an inverse cloze task pre-training objective, preceding both REALM and RAG.
- **Assessment:** Establishes the viability of learned latent retrieval without explicit supervision. Key stepping stone showing that retrieval can be treated as a latent variable in end-to-end NLP systems, directly motivating REALM and RAG.
- **Venue tier:** **Tier-1** (ACL)

#### Source 3: Izacard & Grave 2021 — Fusion-in-Decoder (FiD)
- **Full citation:** Izacard, G. and Grave, E. (2021) 'Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering', *Proceedings of the 16th Conference of the European Chapter of the Association for Computational Linguistics (EACL)*, pp. 874–880.
- **URL:** https://aclanthology.org/2021.eacl-main.74/
- **Relationship:** **Extending** — published concurrently with/shortly after RAG, demonstrates that seq2seq models can efficiently aggregate evidence from many retrieved passages (up to 100), with performance scaling with passage count.
- **Assessment:** Directly relevant as an alternative architecture to RAG's marginalisation approach. FiD's per-passage encoding + shared decoder design is the dominant architecture in later retrieval-augmented systems. Provides evidence that more passages = better performance, relevant to the dissertation's retrieval pipeline design.
- **Venue tier:** **Tier-1** (EACL)

#### Source 4: Weston, Chopra & Bordes 2014 — Memory Networks
- **Full citation:** Weston, J., Chopra, S. and Bordes, A. (2015) 'Memory Networks', *Proceedings of the 3rd International Conference on Learning Representations (ICLR 2015)*.
- **URL:** https://arxiv.org/abs/1410.3916
- **Relationship:** **Foundational** — introduced the paradigm of combining neural inference with an explicit, readable/writable external memory for knowledge-intensive tasks, directly anticipating RAG's non-parametric memory concept.
- **Assessment:** Establishes the theoretical ancestry of retrieval-augmented systems. Memory Networks framed the core insight that neural models benefit from external memory — RAG operationalises this with a dense retrieval index. Essential for the "knowledge-intensive NLP" narrative in the literature review.
- **Venue tier:** **Tier-1** (ICLR)

---

### 1.2 FORWARD CHAINING (Extensions & Critiques)

#### Source 5: Asai et al. 2024 — Self-RAG (already a seed, but noting forward chain)
- **Full citation:** Asai, A., Wu, Z., Wang, Y., Sil, A. and Hajishirzi, H. (2024) 'Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection', *Proceedings of the 12th International Conference on Learning Representations (ICLR 2024)*.
- **URL:** https://openreview.net/forum?id=hSyW5go0v8
- **Relationship:** **Extending** Lewis et al. 2020 — adds adaptive retrieval (retrieve only when needed) and reflection tokens for self-critique, addressing RAG's indiscriminate retrieval.
- **Assessment:** Central to the dissertation's argument that API-based systems cannot use reflection tokens (requires fine-tuning), motivating the external verification + abstention architecture. The paper's 7B/13B models outperform ChatGPT on open-domain QA, demonstrating the value of retrieval self-awareness.
- **Venue tier:** **Tier-1** (ICLR)

#### Source 6: Yao et al. 2025 — SEAKR
- **Full citation:** Yao, Z., Qi, W., Pan, L., Cao, S., Hu, L., Liu, W., Hou, L. and Li, J. (2025) 'SeaKR: Self-aware Knowledge Retrieval for Adaptive Retrieval Augmented Generation', *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (ACL 2025)*, Vienna, pp. 27022–27043. DOI: 10.18653/v1/2025.acl-long.1312.
- **URL:** https://aclanthology.org/2025.acl-long.1312/
- **Relationship:** **Extending/Criticising** Self-RAG — replaces reflection tokens with uncertainty-aware retrieval decisions extracted from LLM internal states, addressing Self-RAG's dependence on fine-tuning.
- **Assessment:** Directly relevant to the dissertation's abstention mechanism. SEAKR's use of model uncertainty to decide *when* to retrieve and *how* to integrate retrieved knowledge parallels the confidence-gating approach. Provides evidence that internal uncertainty signals can replace explicit reflection tokens.
- **Venue tier:** **Tier-1** (ACL)

#### Source 7: Sarthi et al. 2024 — RAPTOR
- **Full citation:** Sarthi, P., Abdullah, S., Tuli, A., Khanna, S., Goldie, A. and Manning, C.D. (2024) 'RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval', *Proceedings of the 12th International Conference on Learning Representations (ICLR 2024)*.
- **URL:** https://openreview.net/forum?id=GN921JHCRw
- **Relationship:** **Extending** RAG — addresses RAG's limitation of retrieving only short contiguous chunks by constructing hierarchical tree structures through recursive summarisation, enabling multi-level abstraction retrieval.
- **Assessment:** Relevant to the dissertation's chunking and retrieval design decisions. RAPTOR's 20% absolute accuracy gain on QuALITY (with GPT-4) demonstrates that flat chunk retrieval leaves significant performance on the table. However, the recursive summarisation adds computational cost that may not be justified at the dissertation's corpus scale.
- **Venue tier:** **Tier-1** (ICLR)

#### Source 8: Barnett et al. 2024 — Seven Failure Points
- **Full citation:** Barnett, S., Kurniawan, S., Thudumu, S., Brber, Z. and Kashyap, M. (2024) 'Seven Failure Points When Engineering a Retrieval Augmented Generation System', *Proceedings of the 2024 IEEE/ACM 3rd International Conference on AI Engineering (CAIN 2024)*. arXiv:2401.05856.
- **URL:** https://arxiv.org/abs/2401.05856
- **Relationship:** **Criticising** — systematic engineering analysis identifying seven distinct failure modes in RAG systems across three case studies (research, education, biomedical).
- **Assessment:** Highly relevant for framing the dissertation's verification layer as addressing specific, empirically-documented failure modes. The finding that "RAG system robustness evolves rather than being designed in" directly supports the audit-trail approach. Complements the theoretical gap analysis with practitioner evidence.
- **Venue tier:** **Tier-2** (IEEE/ACM CAIN)

#### Source 9: Cuconasu et al. 2024 — The Power of Noise
- **Full citation:** Cuconasu, F., Trappolini, G., Siciliano, F., Filice, S., Campagnano, C., Maarek, Y., Tonellotto, N. and Silvestri, F. (2024) 'The Power of Noise: Redefining Retrieval for RAG Systems', *Proceedings of the 47th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR 2024)*.
- **URL:** https://doi.org/10.1145/3626772.3657834
- **Relationship:** **Criticising** — counter-intuitively demonstrates that adding random/irrelevant documents to RAG prompts can improve accuracy by up to 35%, challenging fundamental assumptions about retrieval quality.
- **Assessment:** Critical for the dissertation's argument about reranking necessity. If even noise can help, but high-scoring irrelevant passages actively hurt, the implication is that reranking quality matters more than retrieval recall. Directly motivates the two-stage retrieve-then-rerank architecture.
- **Venue tier:** **Tier-1** (SIGIR)

---

### 1.3 CONFLICTS AND DEBATES

#### Source 10: Liu et al. 2024 — Lost in the Middle
- **Full citation:** Liu, N.F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F. and Liang, P. (2024) 'Lost in the Middle: How Language Models Use Long Contexts', *Transactions of the Association for Computational Linguistics (TACL)*, 12, pp. 157–173.
- **URL:** https://aclanthology.org/2024.tacl-1.9/
- **Relationship:** **Central to RAG vs Long Context debate** — empirically demonstrates that LLMs degrade when relevant information is in the middle of long contexts, a fundamental attention mechanism limitation.
- **Assessment:** Provides the strongest empirical defence of RAG against the "long context makes RAG obsolete" argument. The position bias finding means that even with million-token context windows, retrieval + focused presentation of relevant chunks remains necessary. Directly relevant to the dissertation's retrieval pipeline design.
- **Venue tier:** **Tier-1** (TACL)

**The RAG vs Long Context Debate — Synthesis:**
The debate crystallised in 2024–2025 with models like Gemini (2M tokens) and Claude (1M tokens) prompting "RAG is dead" claims. The evidence resolves as follows:
- **Long context wins** for <100 documents, static corpora, and tasks requiring cross-document reasoning (legal clause cross-referencing).
- **RAG wins** for large/updating corpora (>100K docs), cost-constrained production (2–3 orders of magnitude cheaper), and latency-sensitive applications.
- **Hybrid architectures dominate** in practice: RAG for initial retrieval, long context for final reasoning over 10–20 retrieved chunks.
- **For the dissertation's use case** (university policy corpus, ~50–200 documents, requiring auditability), RAG remains the correct architectural choice because the audit trail requirement demands explicit retrieval provenance that long-context approaches cannot provide.

#### Source 11: RAG Failure Taxonomy (EMNLP 2025 study on distracting passages)
- **Full citation:** (From search results) EMNLP 2025 study finding that over 60% of queries contain at least one highly distracting passage in the top-10 retrieved results, even with state-of-the-art retrieval pipelines.
- **URL:** https://aclanthology.org/2025.emnlp-main.1422.pdf
- **Relationship:** **Criticising** — provides quantitative evidence that retrieval imperfection is the norm, not the exception, in RAG systems.
- **Assessment:** Strengthens the case for the dissertation's multi-stage verification: if 60%+ of queries have distractors in top-10, then post-retrieval filtering (reranking + citation verification) is not optional but essential. This statistic should appear in the literature review to motivate the verification architecture.
- **Venue tier:** **Tier-1** (EMNLP)

---

## CLUSTER 4 — RETRIEVAL + RERANKING

### Seed Papers
- Karpukhin et al. 2020 (DPR) — EMNLP
- Nogueira & Cho 2019 (BERT reranking) — arXiv
- Thakur et al. 2021 (BEIR) — NeurIPS
- Bruch et al. 2023 (fusion functions) — ACM TOIS

---

### 4.1 BACKWARD CHAINING (Foundational Works)

#### Source 12: Robertson & Spärck Jones 1976 — Probabilistic Relevance Weighting
- **Full citation:** Robertson, S.E. and Spärck Jones, K. (1976) 'Relevance weighting of search terms', *Journal of the American Society for Information Science*, 27(3), pp. 129–146.
- **URL:** https://doi.org/10.1002/asi.4630270302
- **Relationship:** **Foundational** — established the probabilistic relevance framework that underlies all subsequent probabilistic retrieval models including BM25. Derived relevance weighting functions from a general probabilistic theory of retrieval.
- **Assessment:** The theoretical root of the entire sparse retrieval branch. Without this, the derivation of BM25 (and hence the BM25 vs dense retrieval debate) lacks mathematical grounding. Essential for establishing the principled basis of the sparse retrieval component in hybrid systems.
- **Venue tier:** **Tier-1** (JASIS — flagship journal of information science)

#### Source 13: Spärck Jones 1972 — Term Specificity / IDF
- **Full citation:** Spärck Jones, K. (1972) 'A statistical interpretation of term specificity and its application in retrieval', *Journal of Documentation*, 28(1), pp. 11–21. DOI: 10.1108/eb026526.
- **URL:** https://www.emerald.com/insight/content/doi/10.1108/eb026526/full/html
- **Relationship:** **Foundational** — proposed that term specificity should be measured statistically (by collection frequency) rather than semantically, establishing the inverse document frequency (IDF) concept that underpins TF-IDF and BM25.
- **Assessment:** The origin point for term weighting in information retrieval. Every sparse retrieval system used in RAG pipelines (BM25, TF-IDF) descends from this insight. Required for a complete intellectual genealogy of the retrieval component.
- **Venue tier:** **Tier-1** (Journal of Documentation — foundational IR venue)

#### Source 14: Robertson et al. 1994 — BM25 / Okapi
- **Full citation:** Robertson, S.E., Walker, S., Jones, S., Hancock-Beaulieu, M.M. and Gatford, M. (1994) 'Okapi at TREC-3', *Proceedings of the Third Text REtrieval Conference (TREC-3)*, NIST Special Publication 500-225, pp. 109–126.
- **Also:** Robertson, S.E. and Walker, S. (1994) 'Some simple effective approximations to the 2-Poisson model for probabilistic weighted retrieval', *Proceedings of the 17th Annual International ACM-SIGIR Conference*, Dublin, pp. 232–241.
- **URL:** https://ir.webis.de/anthology/1994.sigirconf_conference-94.24/
- **Relationship:** **Foundational** — the original formulation and evaluation of the BM25 ranking function, combining term frequency saturation, document length normalisation, and IDF weighting.
- **Assessment:** The most important single sparse retrieval citation. BM25 remains the default baseline in every modern retrieval benchmark (including BEIR). The dissertation's hybrid retrieval pipeline must acknowledge BM25 as the sparse component's theoretical basis.
- **Venue tier:** **Tier-1** (SIGIR + TREC)

#### Source 15: Salton, Wong & Yang 1975 — Vector Space Model
- **Full citation:** Salton, G., Wong, A. and Yang, C.S. (1975) 'A vector space model for automatic indexing', *Communications of the ACM*, 18(11), pp. 613–620. DOI: 10.1145/361219.361220.
- **URL:** https://dl.acm.org/doi/10.1145/361219.361220
- **Relationship:** **Foundational** — established the vector space representation of documents and queries for information retrieval, the conceptual ancestor of all embedding-based retrieval methods.
- **Assessment:** While chronologically distant, the VSM is the intellectual ancestor of dense retrieval: DPR replaces handcrafted TF-IDF vectors with learned BERT embeddings, but the core idea of representing documents as vectors in a space and retrieving by similarity is Salton's. Useful for establishing the long arc from VSM → TF-IDF → BM25 → dense embeddings.
- **Venue tier:** **Tier-1** (Communications of the ACM)

#### Source 16: Bromley et al. 1993 — Siamese Networks
- **Full citation:** Bromley, J., Guyon, I., LeCun, Y., Säckinger, E. and Shah, R. (1993) 'Signature Verification using a "Siamese" Time Delay Neural Network', *Advances in Neural Information Processing Systems 6 (NeurIPS 1993)*, pp. 737–744.
- **URL:** https://proceedings.neurips.cc/paper/1993/hash/288cc0ff022877bd3df94bc9360b9c5d-Abstract.html
- **Relationship:** **Foundational** — introduced the Siamese (dual-encoder) architecture: two identical sub-networks that encode paired inputs independently and compare their representations via a distance metric. This is the architectural ancestor of all bi-encoder retrieval models.
- **Assessment:** Establishes the deep architectural lineage of DPR and modern dense retrieval. The bi-encoder paradigm (encode query and document independently, compare via dot product/cosine) is a direct descendant of Bromley's Siamese architecture. Useful for the cross-attention vs bi-encoder theoretical basis discussion.
- **Venue tier:** **Tier-1** (NeurIPS)

#### Source 17: Reimers & Gurevych 2019 — Sentence-BERT
- **Full citation:** Reimers, N. and Gurevych, I. (2019) 'Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks', *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pp. 3982–3992.
- **URL:** https://aclanthology.org/D19-1410/
- **Relationship:** **Foundational/Extending** — bridged the gap between BERT's cross-encoder architecture and practical embedding-based retrieval by training Siamese BERT networks for efficient sentence-level similarity computation (reducing 65 hours → 5 seconds for 10K sentence comparisons).
- **Assessment:** The critical link between Bromley's Siamese architecture and modern dense retrieval (DPR). SBERT demonstrated that BERT could be adapted into a bi-encoder for scalable semantic similarity, directly enabling the dense retrieval revolution. Relevant to the dissertation's embedding choice for the retrieval component.
- **Venue tier:** **Tier-1** (EMNLP)

---

### 4.2 FORWARD CHAINING (Extensions & Critiques)

#### Source 18: Humeau et al. 2020 — Poly-encoders
- **Full citation:** Humeau, S., Shuster, K., Lachaux, M.-A. and Weston, J. (2020) 'Poly-encoders: Architectures and Pre-training Strategies for Fast and Accurate Multi-sentence Scoring', *Proceedings of the 8th International Conference on Learning Representations (ICLR 2020)*.
- **URL:** https://openreview.net/forum?id=SkxgnnNFvH
- **Relationship:** **Extending** — introduces a middle ground between bi-encoders (fast but less accurate) and cross-encoders (accurate but slow) by learning global attention features rather than token-level cross-attention.
- **Assessment:** Directly relevant to the dissertation's cross-attention vs bi-encoder discussion. Poly-encoders formalize the accuracy-latency trade-off spectrum: bi-encoder → poly-encoder → cross-encoder → full LLM reranking. The dissertation's two-stage architecture (bi-encoder retrieval → cross-encoder reranking) implicitly skips the poly-encoder middle ground, and this paper provides the justification for why that's acceptable at small corpus scale.
- **Venue tier:** **Tier-1** (ICLR)

#### Source 19: Khattab & Zaharia 2020 — ColBERT
- **Full citation:** Khattab, O. and Zaharia, M. (2020) 'ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT', *Proceedings of the 43rd International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR 2020)*, pp. 39–48.
- **URL:** https://doi.org/10.1145/3397271.3401075
- **Relationship:** **Extending** — introduces late interaction as a third paradigm between bi-encoders and cross-encoders: independently encode query and document tokens, then compute fine-grained token-level similarity. Achieves 100x speedup over BERT cross-encoders while maintaining competitive effectiveness.
- **Assessment:** Important for the cross-attention vs bi-encoder theoretical basis section. ColBERT demonstrates that the bi-encoder/cross-encoder dichotomy is a false binary; late interaction retains token-level matching while enabling pre-computation. However, for the dissertation's small corpus (~200 docs), the full ColBERT infrastructure may be over-engineered compared to simple bi-encoder + cross-encoder reranking.
- **Venue tier:** **Tier-1** (SIGIR)

#### Source 20: Sun et al. 2023 — RankGPT (LLM as Reranker)
- **Full citation:** Sun, W., Yan, L., Ma, X., Wang, S., Ren, P., Chen, Z., Yin, D. and Ren, Z. (2023) 'Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents', *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing (EMNLP 2023)*. **Outstanding Paper Award.**
- **URL:** https://aclanthology.org/2023.emnlp-main.923/
- **Relationship:** **Extending/Replacing** — demonstrates that LLMs can perform listwise passage reranking competitively with or superior to supervised cross-encoders, and that this capability can be distilled into smaller models (440M parameter model outperforming 3B supervised model on BEIR).
- **Assessment:** Central to the cross-encoder vs LLM reranking debate. The paper's Outstanding Paper Award at EMNLP signals community recognition. For the dissertation, this establishes LLM reranking as a viable alternative to cross-encoders, but the cost analysis (detailed below) argues against it for production systems.
- **Venue tier:** **Tier-1** (EMNLP — Outstanding Paper Award)

#### Source 21: Bruch et al. 2023 — Fusion Functions (seed paper, noting extensions)
- **Full citation:** Bruch, S., Gai, S. and Ingber, A. (2023) 'An Analysis of Fusion Functions for Hybrid Retrieval', *ACM Transactions on Information Systems*, 42(1), Article 16. DOI: 10.1145/3596512.
- **URL:** https://doi.org/10.1145/3596512
- **Relationship:** **Extending/Criticising** RRF — provides the first systematic comparison of fusion functions, demonstrating that convex combination outperforms RRF in both in-domain and out-of-domain settings, and that RRF is sensitive to its parameters.
- **Assessment:** Directly informs the dissertation's hybrid retrieval fusion choice. If the system uses BM25 + dense retrieval, this paper provides evidence for preferring convex combination over the commonly-used RRF. The sample efficiency finding (small training set suffices for tuning) is relevant to the dissertation's limited policy corpus.
- **Venue tier:** **Tier-1** (ACM TOIS)

---

### 4.3 CONFLICTS AND DEBATES

#### Debate 1: When Does BM25 Beat Dense Retrieval?

**Evidence for BM25 superiority in specific settings:**

#### Source 22: Thakur et al. 2021 — BEIR (seed paper, conflict evidence)
- **Full citation:** Thakur, N., Reimers, N., Rücklé, A., Srivastava, A. and Gurevych, I. (2021) 'BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models', *Proceedings of the 35th Conference on Neural Information Processing Systems (NeurIPS 2021) Datasets and Benchmarks Track*.
- **URL:** https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html
- **Relationship:** **Criticising** DPR — demonstrates that dense retrievers (including DPR) often fail to generalise to out-of-domain tasks in zero-shot settings, while BM25 provides a robust baseline across all 18 datasets.
- **Assessment:** The single most important paper for the BM25 vs dense retrieval debate. BEIR established that DPR's strong performance on Natural Questions does not transfer to other domains, providing the empirical basis for hybrid retrieval. For the dissertation's policy domain (likely out-of-distribution for general dense models), this finding directly motivates the inclusion of BM25 alongside dense retrieval.
- **Venue tier:** **Tier-1** (NeurIPS Datasets & Benchmarks)

**Key empirical findings from the BM25 vs dense retrieval literature:**

| Scenario | Winner | Evidence |
|----------|--------|----------|
| Rare entities/identifiers (e.g., error codes, proper nouns) | BM25 | Dense retrievers encode tokens semantically, treating exact strings as noise (Thakur et al. 2021) |
| Out-of-domain / zero-shot | BM25 | BEIR shows consistent BM25 robustness vs DPR degradation (Thakur et al. 2021) |
| Simple entity-centric questions | BM25 | DPR underperforms on entity lookup (BEIR findings) |
| Semantic similarity / paraphrase matching | Dense | Dense models capture meaning despite lexical variation |
| Complex multi-hop reasoning questions | Dense | Semantic understanding required to chain evidence |
| In-domain with training data | Dense | DPR excels when fine-tuned on domain-specific data (Karpukhin et al. 2020) |

**Resolution for the dissertation:** Hybrid retrieval (BM25 + dense) is the correct choice for the policy domain, where queries may contain exact policy numbers (favouring BM25) or semantic paraphrases (favouring dense). The fusion function choice (convex combination per Bruch et al. 2023) allows tuning the weighting.

#### Debate 2: Cross-Encoder vs LLM Reranking

**Quantitative trade-off summary from the literature:**

| Dimension | Cross-Encoder | LLM (Pointwise) | LLM (Listwise) |
|-----------|---------------|------------------|-----------------|
| NDCG@10 (17 datasets) | ~0.78 (zerank-1) | ~0.70 (GPT-4-mini) | ~0.72 |
| Latency (p50) | ~130ms | 15+ seconds | 500ms–2s |
| Cost per 1,000 queries | ~$2 (Cohere) | $25–30 | $5–15 |
| Pros | Fastest, cheapest, most accurate | — | Cross-document reasoning, flexible criteria |
| Cons | Fixed ranking criteria | Uncalibrated, slow, expensive | Context length limits |

**Source for this analysis:** ZeroEntropy benchmarking (2024–2025); Sun et al. 2023 (EMNLP); Pradeep et al. 2024 (Rank-DistiLLM, ECIR).

#### Source 23: Pradeep et al. 2024 — Rank-DistiLLM
- **Full citation:** Pradeep, R., Hui, K., Gupta, J., Lelkes, A.D., Zhuang, H., Lin, J., Metzler, D. and Tran, V.Q. (2024) 'Rank-DistiLLM: Closing the Effectiveness Gap Between Cross-Encoders and LLMs for Passage Re-Ranking'. arXiv:2405.07920.
- **URL:** https://arxiv.org/abs/2405.07920
- **Relationship:** **Extending** — demonstrates that LLM ranking capabilities can be distilled into cross-encoders, achieving LLM-level effectiveness while being 173x faster and 24x more memory-efficient.
- **Assessment:** Resolves the cross-encoder vs LLM reranking debate by showing distillation can close the gap. For the dissertation, this validates the use of cross-encoder reranking (cheaper, faster) while acknowledging that LLM-distilled cross-encoders represent the frontier.
- **Venue tier:** **Tier-2** (ECIR 2025 / arXiv)

**Resolution for the dissertation:** Cross-encoder reranking is the correct choice for the policy copilot. LLM reranking offers marginal accuracy gains at 10x+ cost and 100x+ latency. At the dissertation's corpus scale, the cross-encoder's 130ms latency fits within interactive response requirements.

#### Debate 3: Chunking Strategy — Semantic vs Fixed-Size

#### Source 24: Qu, Tu & Bao 2025 — Is Semantic Chunking Worth the Computational Cost?
- **Full citation:** Qu, R., Tu, R. and Bao, F. (2025) 'Is Semantic Chunking Worth the Computational Cost?', *Findings of the Association for Computational Linguistics: NAACL 2025*. arXiv:2410.13070.
- **URL:** https://aclanthology.org/2025.findings-naacl.114/
- **Relationship:** **Criticising** semantic chunking — demonstrates through systematic evaluation that semantic chunking's computational costs are not justified by consistent performance gains.
- **Assessment:** Directly relevant to the dissertation's chunking design decision. Key findings: (1) fixed-size chunking outperforms semantic chunking on realistic datasets; (2) for answer generation with GPT-4o, differences are negligible because LLMs compensate for retrieval imperfections; (3) semantic chunking shows marginal benefits only on artificially-constructed datasets. This validates the dissertation's use of paragraph-level chunking.
- **Venue tier:** **Tier-2** (NAACL Findings)

---

## CROSS-CLUSTER CONNECTIONS

### Papers Bridging Clusters 1 and 4

#### Source 25: Exp4Fuse (ACL Findings 2025)
- **Full citation:** (From ACL Findings 2025) 'Exp4Fuse: A Rank Fusion Framework for Enhanced Sparse Retrieval using Large Language Model-based Query Expansion'.
- **URL:** https://aclanthology.org/2025.findings-acl.9/
- **Relationship:** **Extending** — combines LLM-based query expansion with modified RRF, bridging the RAG architecture (Cluster 1) with fusion functions (Cluster 4).
- **Assessment:** Demonstrates the emerging trend of using LLMs not just for generation but also for retrieval enhancement. Relevant to future work directions but may be over-engineered for the dissertation's scope.
- **Venue tier:** **Tier-2** (ACL Findings)

---

## SUMMARY TABLE: ALL 25 SOURCES

| # | Citation | Year | Venue | Tier | Type | Cluster | Already in Matrix? |
|---|----------|------|-------|------|------|---------|-------------------|
| 1 | Guu et al. — REALM | 2020 | ICML | 1 | Foundational | C1 | No — **ADD** |
| 2 | Lee, Chang & Toutanova — ORQA | 2019 | ACL | 1 | Foundational | C1 | No — **ADD** |
| 3 | Izacard & Grave — FiD | 2021 | EACL | 1 | Extending | C1 | No — **ADD** |
| 4 | Weston, Chopra & Bordes — Memory Networks | 2015 | ICLR | 1 | Foundational | C1 | No — **ADD** |
| 5 | Asai et al. — Self-RAG | 2024 | ICLR | 1 | Extending | C1 | Yes (#6) |
| 6 | Yao et al. — SEAKR | 2025 | ACL | 1 | Extending | C1 | No — **ADD** |
| 7 | Sarthi et al. — RAPTOR | 2024 | ICLR | 1 | Extending | C1 | No — **ADD** |
| 8 | Barnett et al. — Seven Failure Points | 2024 | CAIN | 2 | Criticising | C1/C4 | Yes (#47) |
| 9 | Cuconasu et al. — Power of Noise | 2024 | SIGIR | 1 | Criticising | C1/C4 | Yes (#12) |
| 10 | Liu et al. — Lost in the Middle | 2024 | TACL | 1 | Central debate | C1/C4 | Yes (#48) |
| 11 | EMNLP 2025 distracting passages study | 2025 | EMNLP | 1 | Criticising | C1 | No — **ADD** |
| 12 | Robertson & Spärck Jones — relevance weighting | 1976 | JASIS | 1 | Foundational | C4 | No — **ADD** |
| 13 | Spärck Jones — term specificity / IDF | 1972 | J.Doc | 1 | Foundational | C4 | No — **ADD** |
| 14 | Robertson et al. — BM25 / Okapi | 1994 | SIGIR/TREC | 1 | Foundational | C4 | No — **ADD** |
| 15 | Salton, Wong & Yang — Vector Space Model | 1975 | CACM | 1 | Foundational | C4 | No — **ADD** |
| 16 | Bromley et al. — Siamese Networks | 1993 | NeurIPS | 1 | Foundational | C4 | No — **ADD** |
| 17 | Reimers & Gurevych — Sentence-BERT | 2019 | EMNLP | 1 | Foundational | C4 | No — **ADD** |
| 18 | Humeau et al. — Poly-encoders | 2020 | ICLR | 1 | Extending | C4 | No — **ADD** |
| 19 | Khattab & Zaharia — ColBERT | 2020 | SIGIR | 1 | Extending | C4 | No — **ADD** |
| 20 | Sun et al. — RankGPT | 2023 | EMNLP | 1 | Extending | C4 | No — **ADD** |
| 21 | Bruch et al. — Fusion Functions | 2023 | ACM TOIS | 1 | Extending | C4 | Yes (#46) |
| 22 | Thakur et al. — BEIR | 2021 | NeurIPS | 1 | Criticising | C4 | Yes (#45) |
| 23 | Pradeep et al. — Rank-DistiLLM | 2024 | ECIR/arXiv | 2 | Extending | C4 | No — **ADD** |
| 24 | Qu, Tu & Bao — Semantic Chunking | 2025 | NAACL Findings | 2 | Criticising | C4 | Yes (#50) |
| 25 | Exp4Fuse | 2025 | ACL Findings | 2 | Extending | C1/C4 | No — **ADD** |

**Sources to ADD to literature matrix:** 16 new sources (Sources 1–4, 6–7, 11–20, 23, 25)
**Sources already present:** 9 sources (5, 8–10, 21–22, 24, plus partial overlap with existing matrix entries)

---

## INTELLECTUAL GENEALOGY MAPS

### Cluster 1 — RAG System Design Lineage

```
Memory Networks (Weston+ 2014/15)
  └─→ ORQA (Lee+ 2019) — latent retrieval for QA
       └─→ REALM (Guu+ 2020) — retrieval in pre-training
            └─→ RAG (Lewis+ 2020) — retrieval + seq2seq generation
                 ├─→ FiD (Izacard & Grave 2021) — multi-passage fusion
                 ├─→ RARR (Gao+ 2023) — post-hoc attribution
                 ├─→ Attributed QA (Bohnet+ 2022) — evaluation framework
                 ├─→ Self-RAG (Asai+ 2024) — adaptive + reflection
                 │    └─→ SEAKR (Yao+ 2025) — uncertainty-aware retrieval
                 ├─→ RAPTOR (Sarthi+ 2024) — hierarchical retrieval
                 └─→ [Critiques]
                      ├─→ 7 Failure Points (Barnett+ 2024)
                      ├─→ Power of Noise (Cuconasu+ 2024)
                      └─→ Lost in the Middle (Liu+ 2024)
```

### Cluster 4 — Retrieval + Reranking Lineage

```
IDF (Spärck Jones 1972)
  └─→ Probabilistic Relevance (Robertson & Spärck Jones 1976)
       └─→ BM25/Okapi (Robertson+ 1994)
            └─→ [Sparse retrieval baseline in all modern benchmarks]

Vector Space Model (Salton+ 1975)
  └─→ Siamese Networks (Bromley+ 1993)
       └─→ Sentence-BERT (Reimers & Gurevych 2019)
            └─→ DPR (Karpukhin+ 2020) — bi-encoder dense retrieval
                 ├─→ ColBERT (Khattab & Zaharia 2020) — late interaction
                 ├─→ Poly-encoders (Humeau+ 2020) — middle ground
                 └─→ BEIR (Thakur+ 2021) — [showed DPR fails OOD]

BERT Reranking (Nogueira & Cho 2019)
  └─→ RankGPT (Sun+ 2023) — LLM as reranker
       └─→ Rank-DistiLLM (Pradeep+ 2024) — distillation back to cross-encoder

Hybrid Fusion:
  RRF (Cormack+ 2009)
    └─→ Fusion Analysis (Bruch+ 2023) — CC > RRF
         └─→ Exp4Fuse (2025) — LLM-expanded query fusion
```

---

## ACTIONABLE RECOMMENDATIONS FOR THE DISSERTATION

1. **Add backward chain sources (1–4, 12–17)** to the literature review section 2.1/2.2 to establish proper intellectual genealogy. A dissertation-level review must trace RAG back to Memory Networks and REALM, and retrieval back to Spärck Jones/Robertson/Salton.

2. **Use the BM25 vs dense retrieval evidence** (Source 22 + conflict table) to justify hybrid retrieval. The policy domain likely contains both exact identifiers (policy numbers, section references) and semantic queries — the empirical evidence specifically supports hybrid approaches for this use case.

3. **Cite the cross-encoder vs LLM reranking trade-off** (Sources 20, 23 + trade-off table) to defend the cross-encoder reranking choice. The cost/latency analysis provides a quantitative justification: 10x cheaper, 100x faster, with marginal accuracy difference.

4. **Use Qu et al. 2025 (Source 24)** to defend paragraph-level chunking over semantic chunking. The empirical evidence directly supports this design choice.

5. **Use Liu et al. 2024 (Source 10) + the RAG vs long context synthesis** to defend the RAG architecture against the "long context makes RAG obsolete" critique. The audit trail requirement provides an additional, unique argument beyond cost/latency.

6. **Cite SEAKR (Source 6)** as evidence that the field is moving toward uncertainty-aware retrieval, validating the dissertation's confidence-gated abstention mechanism as architecturally aligned with the research frontier.

7. **The EMNLP 2025 distractor finding (Source 11)** — that 60%+ of queries have distracting top-10 passages — should appear in the motivation section to quantify why post-retrieval verification is not optional.
