# Figure and table register — Final report

> **Note:** All figure files under `docs/report/figures/` must be generated before final PDF compilation. Run `python eval/analysis/make_figures.py` for chart figures. Screenshots must be captured manually from the running Streamlit application.

This register lists every figure and table embedded or defined in `docs/report/Final_Report_Draft.md`, with section placement, asset paths, narrative cross-references, and the role each item plays in the argument.

---

## Figures

| ID | Title | Chapter/Section | File path | Referenced in text | What it supports |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Fig 1.1 | PRISMA 2020 flow diagram showing the four-stage literature selection process, from 584 identified records to 38 included studies | Ch. 1 — §1.3 Systematic Search Strategy | `docs/report/figures/fig_prisma.png` | Yes | Visual audit trail for the systematic review; shows how the evidence base for related work was derived. |
| Fig 2.0 | Gantt chart showing the six-sprint development timeline across Weeks 1–22 (October 2024 – February 2025) | Ch. 2 — §2.1 Development Process | `docs/report/figures/fig_gantt.png` | No | Communicates the agile-style sprint plan and temporal scope of implementation work (appears after the sprint list without an in-body “Figure 2.0” call-out). |
| Fig 2.1 | Data flow diagram showing the end-to-end pipeline from PDF ingestion through retrieval, reranking, abstention, generation, and verification | Ch. 2 — §2.3 System Architecture | `docs/report/figures/fig_data_flow.png` | Yes | Makes the modular **Retrieve-and-Rerank-then-Generate-and-Verify** architecture concrete for assessors and future maintainers. |
| Fig 4.1 | Grouped bar chart comparing B1, B2, and B3 across Answer Rate, Abstention Accuracy, Ungrounded Rate, and Evidence Recall@5 | Ch. 4 — §4.2 Headline Results: Baseline Comparison | `docs/report/figures/fig_baselines.png` | Yes | Visual summary of the main baseline ladder results on the test split, complementing Table 4.2. |
| Fig 4.2 | Retrieval quality comparison — B2 vs B3 across Recall@5, MRR, and Precision@5 | Ch. 4 — §4.3 Retrieval Performance | `docs/report/figures/fig_retrieval.png` | No | Supports the claim that cross-encoder reranking improves retrieval ranking and evidence placement (follows Table 4.3 without an explicit “Figure 4.2” sentence). |
| Fig 4.3 | Groundedness metrics — Ungrounded Rate and Citation Precision, before and after verification | Ch. 4 — §4.4 Groundedness and Verification | `docs/report/figures/fig_groundedness.png` | No | Illustrates the impact of the verification layer on faithfulness metrics (paired with Table 4.4 narrative). |
| Fig 4.4 | Threshold sensitivity analysis — Answer Rate vs Abstention Accuracy as a function of the reranker confidence threshold | Ch. 4 — §4.5 Abstention Threshold Sensitivity | `docs/report/figures/fig_tradeoff.png` | Yes | Justifies threshold choice and the coverage–safety trade-off driven by the abstention gate. |
| Fig B.1 | Answerable query result showing extractive fallback with citations | Appendix B — §B.7.3 Streamlit Application Screenshots | `docs/report/figures/screenshot_answerable_query.png` | No | Operational evidence that answerable queries can return cited extractive answers (captioned in appendix only). |
| Fig B.2 | Unanswerable query showing abstention behaviour | Appendix B — §B.7.3 Streamlit Application Screenshots | `docs/report/figures/screenshot_unanswerable_query.png` | No | Demonstrates correct refusal for out-of-corpus questions. |
| Fig B.3 | Contradiction query showing retrieved evidence with citations | Appendix B — §B.7.3 Streamlit Application Screenshots | `docs/report/figures/screenshot_contradiction_query.png` | No | Shows retrieval and citation presentation for contradiction-style queries. |

---

## Tables

| ID | Title | Chapter/Section | Data source | Referenced in text | What it supports |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Table 1.1 | Comparative analysis of retrieval-augmented and grounded generation systems | Ch. 1 — §1.10 Comparative Analysis of Existing Systems | Literature survey / manual synthesis (systems and papers named in table) | Yes | Positions Policy Copilot against prior RAG and grounding approaches across domain, grounding, abstention, and limitations. |
| Table 2.1 | Functional and non-functional requirements with acceptance criteria | Ch. 2 — §2.2 Requirements Analysis | Objectives and scope (§1.2, §1.11); manual specification | Yes (also cited from Table 2.2) | Testable contracts for FR/NFR and traceability to objectives; underpins scope control (e.g. NFR3 deferral). |
| Table 2.2 | Risk register | Ch. 2 — §2.5 Risk Assessment | Project risk review (manual) | Yes | Documents likelihood, impact, and mitigations for API, verification, corpus, scope, threshold calibration, and integrity risks. |
| Table 3.1 | Technology stack and component justification | Ch. 3 — §3.1 Technology Stack | `pyproject.toml` / dependency choices; manual justification text | Yes | Justifies major libraries (embeddings, FAISS, reranker, OpenAI SDK, Pydantic, pdfplumber, pytest, Git). |
| Table 3.2 | Testing and validation matrix | Ch. 3 — §3.8 Testing and Validation | Codebase test layout (`tests/`); manual summary | No | Maps representative test files to tier, component, and validation intent (186 tests, 1 conditionally skipped). |
| Table 4.1 | Golden set composition and evaluation splits | Ch. 4 — §4.1 Experimental Setup | `eval/golden_set/golden_set.csv` (and frozen split definition); counts manual/annotated | No | Defines answerable / unanswerable / contradiction counts and train–test/dev split policy. |
| Table 4.2 | Baseline comparison across primary metrics (test split) | Ch. 4 — §4.2 Headline Results: Baseline Comparison | `scripts/run_eval.py` outputs; `results/runs/*/summary.json` (aggregated for report) | Yes | Headline B1 / B2 / B3 Generative vs Extractive metrics: coverage, abstention, grounding, recall. |
| Table 4.3 | Retrieval metrics — Dense Retrieval (B2) vs. Reranked (B3), test split | Ch. 4 — §4.3 Retrieval Performance | Evaluation JSONL / retrieval logs; summary aggregation | No | Quantifies reranker gains on Recall@*k*, MRR, and Precision@5. |
| Table 4.4 | Groundedness metrics for B3 (Generative), test split | Ch. 4 — §4.4 Groundedness and Verification | Pre/post verification statistics from eval pipeline | Yes | Shows verification’s effect on Ungrounded Rate, Citation Precision, and claims per response. |
| Table 4.5 | Ablation results — B3 with individual components disabled (test split, Generative Mode) | Ch. 4 — §4.6 Ablation Studies | Mixed: B3 Full from final test run; other rows noted in report as design-time / validation-split estimates | No | Attributes reliability gains to reranker, verification, abstention gate, and contradiction detection. |
| Table 4.6 | Critic Mode heuristic detection performance | Ch. 4 — §4.7 Critic Mode Evaluation | Labelled critic test sentences / heuristic eval (project-internal) | No | Pattern-level precision, recall, and F1 vs FR6 target. |
| Table 4.7 | Error taxonomy — B3 failure classification (test split) | Ch. 4 — §4.8 Error Analysis | Manual classification per `eval/analysis/error_taxonomy.md` | No | Breaks failures into over-abstention, retrieval miss, verification FP, etc., with examples. |
| Table 4.7a | End-to-end latency statistics by baseline (ms) | Ch. 4 — §4.8a Latency Performance | Instrumented runs on consumer hardware; OpenAI `gpt-4o-mini` | Yes | Evidence for NFR1 (P95 latency under 10s). |
| Table 4.7b | Human evaluation results (self-administered, 20 queries) | Ch. 4 — §4.8b Human Evaluation | Author ratings on sample of B3 outputs (manual) | No | Qualitative Likert scores for correctness, groundedness, usefulness on answered vs abstention cases. |
| Table 4.7c | Bootstrapped 95% confidence intervals for B3-Generative headline metrics | Ch. 4 — §4.8c Statistical Confidence | Bootstrap (2000 resamples, seed 42) on test-split metrics | No | Uncertainty quantification for small-n evaluation. |
| Table 4.8 | Objective achievement summary | Ch. 4 — §4.9.1 Achievement Against Objectives | Synthesis of reported metrics vs §1.2 targets | Yes | Consolidates pass/partial/fail against each numbered objective. |

“Referenced in text” is **Yes** only if the main narrative includes an explicit cross-reference (e.g. “Table 4.2 …”, “Figure 4.4 …”). Items introduced only by heading or placement alone are marked **No**.

---

## Generated evaluation tables (new in Final Maximiser phase)

| ID | Title | File | What it supports |
| :--- | :--- | :--- | :--- |
| — | Failure-mode taxonomy counts per baseline | `results/tables/failure_taxonomy.csv` | Error Analysis (§4.8) — diagnostic breakdown |
| — | Auditability rubric scores per baseline | `results/tables/auditability_scores.csv` | Evaluation protocol (§4) — 5-axis auditability profile |
| — | Ablation comparison delta table | `results/tables/ablation_comparison.csv` | Ablation Studies (§4.6) — side-by-side metric deltas |
| — | Objective slice evaluation results | `results/tables/objective_slice_results.csv` | Objective task slice (§4) — deterministic query subset |
| — | Cross-run summary with all metrics | `results/tables/run_summary.csv` | Baseline comparison (§4.2) — aggregated from make_figures.py |

## Missing figures (require manual capture or generation)

The following PNG paths are referenced in the report. Chart figures (fig_baselines, fig_retrieval, fig_groundedness, fig_tradeoff) now exist under `results/figures/` and should be copied to `docs/report/figures/` before PDF compilation. Remaining items require manual creation:

| Expected path | Kind |
| :--- | :--- |
| `docs/report/figures/fig_prisma.png` | Diagram (PRISMA) — typically external tool or manual figure |
| `docs/report/figures/fig_gantt.png` | Timeline chart — manual or tooling outside `make_figures.py` |
| `docs/report/figures/fig_data_flow.png` | Architecture diagram — manual or external export |
| `docs/report/figures/fig_baselines.png` | Chart — `eval/analysis/make_figures.py` |
| `docs/report/figures/fig_retrieval.png` | Chart — `eval/analysis/make_figures.py` |
| `docs/report/figures/fig_groundedness.png` | Chart — `eval/analysis/make_figures.py` (requires B3 generative eval data / API per report appendix note) |
| `docs/report/figures/fig_tradeoff.png` | Chart — `eval/analysis/make_figures.py` |
| `docs/report/figures/screenshot_answerable_query.png` | Streamlit screenshot — manual |
| `docs/report/figures/screenshot_unanswerable_query.png` | Streamlit screenshot — manual |
| `docs/report/figures/screenshot_contradiction_query.png` | Streamlit screenshot — manual |

After generating charts and capturing screenshots, re-check that each file exists next to the draft before compiling the final PDF.
