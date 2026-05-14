# Reference Audit

Last updated: May 2026

## Summary

- **Total references in List of References:** 37
- **Total unique in-text citations:** 37
- **Citation style:** Leeds Harvard (Author, Year)
- **Orphan references (listed but never cited):** 0
- **Missing references (cited but not listed):** 0
- **Source-tier note:** all listed references are peer-reviewed scholarly sources that survived the §1.3 PRISMA-aligned inclusion criteria. The two earlier contextual entries (Deloitte AI Institute 2024 and Kamradt 2024) were removed during the May-2026 audit pass: the Deloitte page was no longer reliably accessible, and the Pinecone URL serves a different article than the one previously cited. The surrounding prose was rewritten so the scholarly evidence base carries the argument without those two contextual citations.

## Audit Actions Taken

| Issue | Action |
|-------|--------|
| Page et al. (2021) cited in §1.3 but missing from reference list | Added full PRISMA 2020 reference |
| Barnett et al. (2024) author name typo ("Brber" → "Barber") | Corrected |
| Chen et al. (2024) — listed but never cited in body | Removed |
| Kamalloo et al. (2023) — listed but never cited in body | Removed |
| Nogueira et al. (2020) — listed but never cited (Nogueira and Cho, 2019 IS cited) | Removed |
| Reference list not sorted alphabetically | Sorted A→Z by first author surname |

## Citation Coverage by Chapter

| Chapter | Citations | Notes |
|---------|-----------|-------|
| Summary | 0 | No citations expected |
| Ch 1: Introduction & Background | 28 | Strongest citation density; covers RAG, hallucination, retrieval, legal NLP, abstention, evaluation, comparative analysis, gap analysis |
| Ch 2: Methodology | 5 | Primarily cites evaluation frameworks and design justification sources |
| Ch 3: Implementation | 5 | Cites Brown et al. (prompting), Nogueira & Cho (reranking), Qu et al. (chunking) |
| Ch 4: Results & Discussion | 8 | Cites evaluation/comparison sources to contextualise findings |
| Appendix A | 2 | Strubell et al. (environmental), Es et al. (RAGAS) |
| Appendix B | 0 | External materials declaration — no citations expected |

## Research Pack Alignment

| Research pack file | Sources | Status |
|-------------------|---------|--------|
| `docs/research/literature_matrix.md` | 105 | Complete — 59 T1, 27 T2, 19 T3 |
| `docs/research/comparator_matrix.md` | 10 systems | Complete |
| `docs/research/search_strategy.md` | PRISMA flow documented | Complete |
| `docs/research/gap_statement.md` | — | Complete |
| `docs/research/taxonomy_of_related_work.md` | — | Complete |
| `docs/research/dissertation_benchmark_report.md` | 13 comparators + 6 ref systems | Complete |

## Remaining Manual Checks

- Verify all "Accessed:" dates on web sources are accurate
- Confirm page ranges for conference proceedings are correct against publisher records

## Audit-driven corrections (May 2026)

Applied per the strict audit `final_dissertation_consistency_audit.pdf`. Each row is the publisher source the audit cited as evidence; the report bibliography and any in-text citations were updated to match.

| Reference | Action | Audit evidence |
|---|---|---|
| Barnett et al. (2024) — RAG seven failure points | Author list corrected to Barnett, S., Kurniawan, S., Thudumu, S., Brannelly, Z. and Abdelrazek, M.; added doi:10.1145/3644815.3644945 | https://dl.acm.org/doi/10.1145/3644815.3644945; https://arxiv.org/abs/2401.05856 |
| Cuconasu et al. (2024) — Power of Noise | Author list expanded to the full eight authors; added doi:10.1145/3626772.3657834 | https://arxiv.org/abs/2401.14887; https://dl.acm.org/doi/10.1145/3626772.3657834 |
| ASPIRE | Replaced Pei et al. (2023) with Chen, J., Yoon, J., Ebrahimi, S., Arik, S., Pfister, T. and Jha, S. (2023). Findings of EMNLP 2023, pp.5190-5213. doi:10.18653/v1/2023.findings-emnlp.345. In-text citations updated Pei → Chen | https://aclanthology.org/2023.findings-emnlp.345/ |
| RAGAS | Updated to formal venue: Es, S., James, J., Espinosa-Anke, L. and Schockaert, S. (2024). EACL Demo, pp.150-158 | https://aclanthology.org/2024.eacl-demo.16/ |
| RAGE | Replaced Zhang, X., Gao, M. and Chen, D. (2024) with Penzkofer, V. and Baumann, T. (2024). KONVENS 2024, pp.57-64. In-text citations updated Zhang → Penzkofer and Baumann | https://aclanthology.org/2024.konvens-main.6/ |
| Yue et al. (2023) — attribution evaluation | Corrected to Yue, X., Wang, B., Chen, Z., Zhang, K., Su, Y. and Sun, H. (2023). Findings of EMNLP 2023, pp.4615-4635. doi:10.18653/v1/2023.findings-emnlp.307 | https://aclanthology.org/2023.findings-emnlp.307/ |
| Lost in the Middle | Year corrected from 2023 to 2024 (TACL vol 12 was published 2024); rest of entry unchanged | https://aclanthology.org/2024.tacl-1.9/ |
| Kamradt / Pinecone | Removed bibliography entry (audit notes the Pinecone URL now resolves to a different 2025 article); §3.2 prose reworded to "practitioner discussions of chunking strategies (e.g., open-source tutorials and vendor blog posts)" without an attributed reference. The methodological argument already rested on Qu, Bao and Tu (2024), which remains cited | https://www.pinecone.io/learn/chunking-strategies/ (now serves a different article) |
| Deloitte AI Institute (2024) | Removed bibliography entry and removed the citing sentence in §1.1; the surrounding paragraph still establishes the compliance-cost concern via Ji et al. (2023) and Huang et al. (2023) | (audit confirmed source not reliably accessible) |
| Johnson, Douze and Jégou (FAISS) | Aligned to the IEEE journal form: (2021), IEEE Transactions on Big Data 7(3), pp.535-547, doi:10.1109/TBDATA.2019.2921572. In-text citation year updated from 2019 to 2021 to match the journal publication year | https://ieeexplore.ieee.org/document/8733051 |
| Bohnet et al. (2022) — Attributed QA | Author list shortened to 'Bohnet, B. et al.' to reflect the 22-author paper; arXiv:2212.08037 retained | https://arxiv.org/abs/2212.08037 |
| Gao et al. (2023) — RARR | Final author corrected from 'Chang, K.' to 'Guu, K.'; 'Juan, D.' updated to 'Juan, D.-C.'; 'Zhao, V.Y.' simplified to 'Zhao, V.' to match the ACL Anthology author list | https://aclanthology.org/2023.acl-long.910/ |
| Guha et al. (2023) — LegalBench | Author list shortened to 'Guha, N. et al.' to reflect the large multi-author paper; venue confirmed as NeurIPS 36, pp.44123-44279 | https://proceedings.neurips.cc/paper_files/paper/2023/hash/89e44582fd28ddfea1ea4dcb0ebbf4b0-Abstract-Datasets_and_Benchmarks.html |
| Ren et al. (2023) — factual knowledge boundary | Author list corrected to 'Ren, R., Wang, Y., Qu, Y., Zhao, W.X., Liu, J., Tian, H., Wu, H., Wen, J.-R. and Wang, H.' per the arXiv record | https://arxiv.org/abs/2307.11019 |
| Zheng et al. (NeurIPS 2023 — MT-Bench) | Year corrected from 2024 to 2023 to match the NeurIPS 36 (2023) publication; in-text citations updated accordingly | https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html |

## Unresolved

None at submission time. All audit-flagged entries above have been resolved using publisher-level evidence.
