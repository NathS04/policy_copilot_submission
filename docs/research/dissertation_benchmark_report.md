# Policy Copilot — Dissertation Benchmark Report

## 1. EXECUTIVE VERDICT

**Overall position:** Policy Copilot's feature set — citation enforcement, abstention, contradiction handling, critic mode, audit export, experiment explorer, reviewer mode, 186-test reproducibility harness — already exceeds the median student RAG dissertation on system scope. Most student RAG projects stop at "chat over PDFs plus embedding model comparison." Your project goes substantially further.

**But scope alone does not win marks.** The strongest comparators in this benchmark set win by making their claims *measurable, reproducible, and reviewer-facing*. The gap between "strong codebase" and "elite dissertation" is not more features — it is proof.

### Top 5 remaining gaps most likely to cost marks

1. **No failure-mode taxonomy.** The Oxford MSc (C1) categorises every error into retrieval-failure vs generation-failure vs contradiction-failure and reports distributions per configuration. Policy Copilot has error analysis but no structured taxonomy with per-module breakdowns.

2. **"Audit-ready" is not yet a measurable claim.** You need a rubric that separately scores retrieval relevance, citation faithfulness, abstention correctness, and contradiction handling — then reports results against it. Without this, "audit-ready" is branding, not science.

3. **No "objective slice" evaluation.** C16 (JKU Linz VAT) picks a question type where correctness is deterministically checkable. Policy Copilot evaluates on a golden set, but the golden set does not isolate an objectively gradable task family that eliminates LLM-judge subjectivity criticism.

4. **Risk audit table missing from the report.** C1 includes a structured risk table (threat, mitigation, logging, residual risk). For a project whose identity is "audit-ready," this is a near-mandatory report artefact.

5. **Evidence rail metadata not maximally screenshot-worthy.** C15 (Lund clinical pharmacology) displays retrieval scores, document types, section IDs, and a copyable reference format alongside a prominent "insufficient context" warning. Policy Copilot's UI has these elements but may not be presenting them at the screenshot-density level examiners need.

---

## 2. BENCHMARK SET

### Scoring key
Orig = originality, Scope = technical scope, Arch = architecture complexity, Eval = evaluation depth, Repro = reproducibility/engineering hygiene, UI = product polish, Trust = explainability/evidence design, Abl = baselines/ablations, Write = report quality, Serious = dissertation-grade seriousness. All 1–5. Similarity = usefulness for benchmarking Policy Copilot (0–5).

### C1 — Retrieval-Augmented AI Assistants for Healthcare: System Design and Evaluation
- **Institution:** University of Oxford
- **Year:** 2025
- **Level:** MSc (Software Engineering)
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [ORA Record](https://ora.ox.ac.uk/objects/uuid:9add0c17-f4fe-4051-9a2a-027f8818a5aa), [PDF](https://ora.ox.ac.uk/objects/uuid:9add0c17-f4fe-4051-9a2a-027f8818a5aa/files/d3197xm748)
- **Artefacts:** Report YES, Code NOT PUBLICLY LINKED, UI figures in-report YES, Evaluation YES
- **Similarity:** 5/5
- **Assessment:** Orig 4 · Scope 5 · Arch 5 · Eval 5 · Repro 4 · UI 4 · Trust 5 · Abl 5 · Write 5 · Serious 5
- **Verdict:** The strongest single comparator. Failure-mode taxonomy, parameter grid search, risk audit table, ELSI chapter, synthetic data for privacy, "Unknown" and "Contradictory" as first-class evaluation categories. This is the template to beat.

### C2 — Retrieval Augmented Generation on Regulatory Documents
- **Institution:** Athens University of Economics and Business (AUEB)
- **Year:** 2025
- **Level:** BSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE (reports 4th retrieval / 3rd generation in RIRAG 2025 shared task)
- **Links:** [PDF](https://nlp.cs.aueb.gr/theses/bsc_thesis_chasandras.pdf), [GitHub](https://github.com/nlpaueb/verify-refine-repass)
- **Artefacts:** Report YES, Code YES, UI NO, Evaluation YES (shared-task + experiments)
- **Similarity:** 5/5
- **Assessment:** Orig 5 · Scope 5 · Arch 5 · Eval 5 · Repro 4 · UI 2 · Trust 5 · Abl 5 · Write 4 · Serious 5
- **Verdict:** Strongest domain match. Regulatory/policy QA, contradiction and obligation coverage, iterative refinement loops, external competitive evaluation context.

### C3 — AuditRAG: An ARAG Approach for Auditing Dutch Annual Reports
- **Institution:** Vrije Universiteit Amsterdam
- **Year:** 2025
- **Level:** MSc (Business Analytics)
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://vu-business-analytics.github.io/internship-office/reports/report-bijvoet.pdf), [GitHub](https://github.com/Larsokillerz/AuditRAG)
- **Artefacts:** Report YES, Code YES (public GitHub), UI limited, Evaluation YES (5 professional auditors, 86% accuracy)
- **Similarity:** 5/5
- **Assessment:** Orig 4 · Scope 5 · Arch 5 · Eval 5 · Repro 4 · UI 2 · Trust 4 · Abl 5 · Write 4 · Serious 5
- **Verdict:** NEW comparator not in original benchmark PDF. Strongest "audit" domain match: agentic RAG for real compliance verification, professional auditor validation, ablation studies, local-first privacy. Public code repo is a major strength.

### C4 — Automating the Maturity Model for Audit and Compliance
- **Institution:** University of Padua
- **Year:** 2024/2025
- **Level:** MSc (Cybersecurity)
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [Thesis record](https://thesis.unipd.it/handle/20.500.12608/89889)
- **Artefacts:** Report YES, Code NOT PUBLICLY LINKED, UI NO, Evaluation YES (82% precision, 86.2% recall)
- **Similarity:** 4/5
- **Assessment:** Orig 4 · Scope 4 · Arch 4 · Eval 4 · Repro 3 · UI 1 · Trust 3 · Abl 3 · Write 4 · Serious 4
- **Verdict:** NEW comparator. RAG for automating audit compliance checks against maturity model. Good evaluation but no UI, no public code.

### C5 — AI-Assisted Compliance: Corporate Governance Reporting with RAG
- **Institution:** Tilburg University
- **Year:** 2025
- **Level:** MSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://arno.uvt.nl/show.cgi?fid=189914)
- **Artefacts:** Report YES, Code NO, UI NO, Evaluation YES
- **Similarity:** 4/5
- **Assessment:** Orig 4 · Scope 3 · Arch 3 · Eval 4 · Repro 2 · UI 1 · Trust 3 · Abl 3 · Write 4 · Serious 4

### C6 — Congressional Hearings QA Pipeline with RAG
- **Institution:** Delft University of Technology
- **Year:** 2025
- **Level:** BSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://repository.tudelft.nl/file/File_18848857-f99a-4664-88b6-997eca491e1a)
- **Artefacts:** Report YES, Code YES, Evaluation YES
- **Similarity:** 4/5
- **Assessment:** Orig 3 · Scope 4 · Arch 4 · Eval 4 · Repro 4 · UI 1 · Trust 3 · Abl 4 · Write 3 · Serious 4

### C7 — LLM Agent as Insurance Law Assistant
- **Institution:** Aalto University
- **Year:** 2024
- **Level:** MSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://aaltodoc.aalto.fi/bitstreams/a44ccb07-e09a-491a-8452-7b75501db27e/download)
- **Artefacts:** Report YES, Code NO, UI YES (web app), Evaluation YES (expert scoring)
- **Similarity:** 4/5
- **Assessment:** Orig 4 · Scope 4 · Arch 4 · Eval 3 · Repro 2 · UI 4 · Trust 4 · Abl 2 · Write 4 · Serious 4

### C8 — Development and Evaluation of RAG Methods for Document Search
- **Institution:** Tampere University
- **Year:** 2025
- **Level:** MSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://trepo.tuni.fi/bitstream/10024/227255/2/KorkeeRoope.pdf)
- **Artefacts:** Report YES, Code NO, Evaluation YES (noise/adversarial concerns)
- **Similarity:** 4/5
- **Assessment:** Orig 3 · Scope 4 · Arch 4 · Eval 4 · Repro 3 · UI 1 · Trust 3 · Abl 4 · Write 4 · Serious 4

### C9 — AcademicRAG: Knowledge Graph Enhanced RAG for Academic Resource Discovery
- **Institution:** KTH Royal Institute of Technology
- **Year:** 2025
- **Level:** MSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [DIVA Record](https://www.diva-portal.org/smash/record.jsf?pid=diva2%3A1971383)
- **Artefacts:** Report YES, Code NOT PUBLICLY LINKED, UI (Research Assistant Tool), Evaluation YES
- **Similarity:** 3/5
- **Assessment:** Orig 4 · Scope 4 · Arch 4 · Eval 4 · Repro 3 · UI 3 · Trust 3 · Abl 3 · Write 4 · Serious 4
- **Verdict:** NEW comparator. GraphRAG approach with knowledge graph integration. Strong architecture but different domain.

### C10 — Using LLMs for Legal Decision-Making in Austrian VAT Law
- **Institution:** Johannes Kepler University Linz
- **Year:** 2025
- **Level:** MSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://www.dke.uni-linz.ac.at/rest/dke_web_res/publications/theses/MT2507/MT2507_copy.pdf)
- **Artefacts:** Report YES, Code NO, Evaluation YES (RAG vs fine-tuning)
- **Similarity:** 5/5
- **Assessment:** Orig 4 · Scope 4 · Arch 4 · Eval 4 · Repro 2 · UI 1 · Trust 4 · Abl 4 · Write 4 · Serious 4
- **Verdict:** The "objective slice" exemplar. Picks a deterministically gradable legal task (place-of-supply determination) to eliminate evaluation subjectivity.

### C11 — RAG Pipeline for Clinical Pharmacology
- **Institution:** Lund University
- **Year:** 2026
- **Level:** BSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://lup.lub.lu.se/luur/download?fileOId=9218372&func=downloadFile&recordOId=9217999)
- **Artefacts:** Report YES, Code NO, UI YES (prototype with evidence display + warnings), Evaluation YES (expert feedback)
- **Similarity:** 4/5
- **Assessment:** Orig 4 · Scope 4 · Arch 4 · Eval 3 · Repro 2 · UI 4 · Trust 4 · Abl 2 · Write 4 · Serious 4
- **Verdict:** Best UI trust pattern to steal: explicit "insufficient context" warnings, evidence chunks with IDs, retrieval scores, document types, copyable reference format.

### C12 — Document-Centric QA System for AUEB Studies Guide
- **Institution:** Athens University of Economics and Business
- **Year:** 2025
- **Level:** BSc thesis
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [PDF](https://nlp.cs.aueb.gr/theses/n_mitsakis_bsc_thesis.pdf)
- **Artefacts:** Report YES, Code NO, Evaluation YES (multi-granularity + IR + LLM evaluation)
- **Similarity:** 5/5
- **Assessment:** Orig 4 · Scope 5 · Arch 5 · Eval 5 · Repro 3 · UI 1 · Trust 4 · Abl 5 · Write 4 · Serious 5
- **Verdict:** Blueprint for engineering + evaluation depth in a bounded document domain. Multi-granularity indexing (chunks/sentences/propositions) creates ablation axes.

### C13 — FinLLM RAG Evaluation Pipeline
- **Institution:** Unknown (thesis work, public GitHub)
- **Year:** 2025
- **Level:** Student thesis (level unclear)
- **Grade:** GRADE NOT PUBLICLY VISIBLE
- **Links:** [GitHub](https://github.com/0xBuro/FinLLM-RAG-Eval)
- **Artefacts:** Code YES (public), Report NOT PUBLICLY LINKED, Evaluation YES (RAGAS, faithfulness)
- **Similarity:** 3/5
- **Assessment:** Orig 3 · Scope 3 · Arch 3 · Eval 4 · Repro 4 · UI 1 · Trust 3 · Abl 3 · Write 2 · Serious 3
- **Verdict:** NEW comparator. Good evaluation pipeline hygiene (RAGAS, faithfulness metrics, SEC filings). Strong repo structure.

### Non-student reference systems (ideas only, not grading comparators)
- **R1: RAGAS** — Reference-free evaluation framework for RAG (metrics spanning retrieval + generation)
- **R2: TruLens** — RAG triad: context relevance, groundedness, answer relevance
- **R3: LangSmith** — Annotation queues for structured human feedback on traces
- **R4: Langfuse** — LLM observability with evaluation, experiments/datasets, self-hosting
- **R5: LedgerRAG** (2026 paper) — Governance-driven agentic chain of retrieval with explicit claim-level evidence ledger, conflict governance (CRAcc 0.993), trigger-based retrieval refresh
- **R6: Citation-Enforced RAG for Fiscal Document Intelligence** (2026 paper) — Page-level provenance, abstention-aware decision policy, paragraph-level citation enforcement for tax compliance

---

## 3. TOP-TIER COMPARATORS

### 1. C1 (Oxford MSc healthcare RAG)
The closest "dissertation-grade auditability" mirror. Failure-mode taxonomy mapping engineering choices to ethical risk, parameter grid search with cost/latency trade-offs, synthetic data for privacy-respecting evaluation, "Unknown" and "Contradictory" as first-class behaviours, risk audit table, dedicated ELSI chapter. This is the evaluation standard to beat.

### 2. C2 (AUEB regulatory documents)
Strongest domain match for Policy Copilot. Regulatory QA with precision requirements, shared-task competitive context (RIRAG 2025), contradiction and obligation coverage metrics, iterative refinement with stepwise progression reporting. Demonstrates that "policy compliance assistant" claims can be backed by domain-specific metrics.

### 3. C3 (VU Amsterdam AuditRAG)
Strongest "audit" keyword match: agentic RAG verifying real Dutch annual reports against regulatory requirements, validated by 5 professional auditors (86% accuracy), ablation studies confirming each agent's contribution, public GitHub repo, local-first privacy design. Demonstrates that audit-domain RAG can be evaluated rigorously with real practitioners.

### 4. C12 (AUEB document-centric student support)
Blueprint for engineering + evaluation depth: multi-granularity document representations (chunks, sentences, propositions), hybrid retrieval, evaluation combining classical IR metrics with LLM-based assessment. Even though the domain is student guides, the structure maps directly to policy: authoritative corpus, bounded coverage, grounding constraints.

### 5. C10 (JKU Linz VAT law)
Shows how to defend "compliance assistant" claims with controlled experimental framing: RAG vs fine-tuning comparison, objectively gradable legal task (place-of-supply determination), semantically searchable legal corpus. The "choose an objectively gradable slice" move is a major dissertation-strengthener.

---

## 4. WHAT THEY DO BETTER THAN ME

### UI / aesthetics
- **C11 (Lund)** stages evidence as a first-class UI object: retrieval scores, document types, section IDs, copyable reference format, and a prominent "insufficient context" warning
- **C1 (Oxford)** includes multiple UI artefacts in-document: upload flow, chat UI, parameter grid search interface, annotation tool
- Policy Copilot has these elements but may not be presenting them at the screenshot-density level that examiners need to see

### Evaluation
- **C1** demonstrates the gold-standard pattern: split evaluation into retrieval relevance, response correctness, and failure-mode attribution; enforce "Unknown" and "Contradictory" behaviours; audit AI-judge labels with manual review
- **C2** evaluates through a domain-specific metric (RePASs) and reports stepwise progression through iterative refinement
- **C3** uses 5 professional auditors for validation — real human expert evaluation
- **C12** evaluates across multiple document granularities combining classical IR + LLM-based evaluation
- **C10** picks an objectively gradable slice eliminating evaluation subjectivity

### System scope
- Top comparators often pick a tightly bounded corpus and define "correctness" precisely (C10's VAT, C12's studies guide). This scoping move reduces examiner pushback

### Reproducibility
- **C1** explicitly tracks token usage and latency as part of design trade-off analysis
- **C8** includes an explicit "Use of AI in thesis" disclosure section
- **C3** provides full public GitHub with all code

### Research depth
- **C12's** multi-granularity representation is a research move creating ablation axes
- **C10's** RAG vs fine-tuning comparison is a research move showing understanding of alternative adaptation strategies

### Report / presentation
- **C1** includes risk audit table, ELSI chapter, appendices with prompts and data, and high figure density
- **C2** includes structured appendices for prompts and algorithm listings

---

## 5. WHAT I ALREADY DO BETTER

Based on what Policy Copilot's codebase actually contains:

- **Citation enforcement + abstention + contradiction handling as explicit product features** — aligns with the most rigorous comparators' evaluation-driven behaviours. Most student projects have none of these three.
- **Critic mode (L1-L6 policy language analysis)** — no comparator has anything equivalent. This is genuinely novel scope.
- **Audit export (JSON + HTML)** — most comparators are notebook-centric or demo-centric. Having structured export is a real differentiator.
- **Reviewer mode with rubric capture** — closer to "system as research instrument" than most theses
- **Experiment explorer** — allows inspection of baseline comparisons, run manifests, per-query outcomes
- **186-test reproducibility harness** with smoke scripts, artifact verification, offline reproduction — exceeds all comparators except possibly C1
- **105-source research pack** with citation chaining, taxonomy, gap statement — exceeds the typical student bibliography
- **Hybrid retrieval (RRF)** as a real implementation, not just discussed
- **Service layer architecture** separating UI from business logic — most student projects pack everything into notebooks or a single script
- **Multi-mode UI** (Ask, Audit Trace, Critic Lens, Experiment Explorer, Reviewer) — far beyond the typical single-page demo

The caution from the benchmark report is correct: **these advantages only count if demonstrated and measured, not merely described.**

---

## 6. IMPROVEMENT EXTRACTION

### Highest mark impact

| Improvement | Source | Why it matters | Effort | Impact | Affects |
|------------|--------|---------------|--------|--------|---------|
| **Failure-mode taxonomy** — categorise every evaluation error into retrieval-failure / generation-failure / contradiction-failure / abstention-failure and report distributions per baseline | C1 | Examiners reward diagnostic evaluation. Turns "RAG feels better" into "here is what fails and why" | Med | HIGH | write-up, appendices |
| **Two-axis evaluation rubric** — separate labels for retrieval relevance and response correctness, plus enforce "Unknown" and "Contradictory" as first-class evaluated outcomes | C1 | Converts "audit-ready" from branding to assessable claim | Med | HIGH | research pack, write-up |
| **Risk audit table** — structured table of risks, mitigations, logging, residual risk for a compliance assistant | C1 | Looks professional, aligns with "audit-ready" claim, signals maturity | Low | HIGH | write-up, appendices |
| **"Objective slice" evaluation** — choose a question subtype where answers are deterministically checkable (e.g., clause ID + obligation/permission classification) | C10 | Reduces "LLM evaluation subjectivity" criticism | Med | HIGH | research pack, write-up |
| **Stepwise progression tables** — show metrics after each pipeline stage (retrieve, verify, contradiction refine) | C2 | Makes pipeline scientifically legible and ablation-friendly | Low-Med | HIGH | write-up, appendices |

### Medium mark impact

| Improvement | Source | Why it matters | Effort | Impact | Affects |
|------------|--------|---------------|--------|--------|---------|
| **Token/cost/latency trade-off reporting** per configuration | C1, C8 | Compliance contexts care about operational constraints | Low-Med | MED-HIGH | write-up |
| **"Use of AI in thesis" disclosure** + prompt appendix | C8, C2 | Increasingly expected; reduces ethics/process friction | Low | MED | write-up, appendices |
| **Evidence rail metadata upgrade** — retrieval scores, section/page references, document type, copyable reference format, prominent "insufficient context" warning | C11 | Makes trust visible; highest screenshot-to-mark ratio | Med | MED-HIGH | UI, write-up |
| **Adversarial/noisy query robustness tests** | C8 | Shows understanding of deployment threats | Med | MED | research pack, write-up |

### Polish-only (do after evaluation is defensible)

| Improvement | Source | Why it matters | Effort | Impact | Affects |
|------------|--------|---------------|--------|--------|---------|
| **Demo storyline scripts** — 3 scripted journeys (happy path, abstention, contradiction) | C1 | Helps viva/demo performance | Low | LOW | presentation |
| **Visual design tightening** — consistent icons for cited/uncited/contradiction/abstained states | C11 | Improves perceived professionalism | Low | LOW | UI |

---

## 7. AESTHETICS / UI IDEAS WORTH COPYING

1. **Evidence rail with metadata** (C11): Source chunks displayed with IDs, retrieval scores, document types, and copyable reference format. Replace "PMID" with policy clause ID / section / page. Screenshot target: one Q&A with evidence rail expanded + a visible "insufficient evidence" warning state.

2. **Contradiction banner + conflict set panel** (C1, C2): Treat contradiction as a first-class UI object. Show conflicting snippets side-by-side + why they conflict + system resolution (abstained / reported both). Screenshot target: a query triggering contradiction mode.

3. **Reviewer workflow UI** (C1, R3): Queue → rubric → decision → export. Screenshot target: experiment explorer with item selected, rubric visible, decision logged.

4. **Experiment explorer as instrument** (C1): Configuration diffs, metric deltas, direct links to example failures. Screenshot target: configuration comparison with cost/latency + faithfulness metrics.

5. **One-click audit export** producing a structured packet: question, answer, evidence excerpts, retrieval scores, model config, timestamps, decision log.

---

## 8. DISSERTATION DOCUMENTATION IDEAS WORTH COPYING

1. **Requirements → testable claims** (C1): Define functional + non-functional requirements for "audit-ready" and map each to a test or evaluation metric. Policy Copilot already has FR1-FR6 and NFR1-NFR4; the report must close the loop by showing each is satisfied.

2. **Evaluation chapter with "method sheet" clarity** (C1): Metrics, rubrics, token/cost/latency measurement, failure taxonomy, then case studies + quantitative findings. The quant + qualitative combination is a dissertation strength pattern.

3. **Risk audit table** (C1): Threat model, mitigation, logging, residual risk, failure containment. For a compliance/policy tool, this is near-mandatory.

4. **Appendix discipline** (C2, C8): Prompts, rubrics, datasets, reproducibility notes, AI tool usage disclosure. Every appendix should serve a defensive purpose.

5. **Figure density over narrative density** (C1): Every major claim gets a figure or table. Your dissertation should be "visually defensible."

6. **Stepwise progression** (C2): Show metrics improving through pipeline stages, not just final numbers.

---

## 9. FINAL PRIORITISED BACKLOG FOR MY PROJECT

### Highest mark impact — do before submission

| # | Exact change | Why it matters | Still worth it? |
|---|-------------|---------------|----------------|
| 1 | **Add a failure-mode taxonomy** to the evaluation chapter: classify every golden-set error into retrieval-miss / generation-hallucination / contradiction-miss / abstention-error; report distributions per baseline (B1/B2/B3) | Converts evaluation from "numbers in a table" to "diagnostic understanding." Examiners love this. | YES — even a small taxonomy over your 63 golden-set queries is powerful |
| 2 | **Create a two-axis evaluation rubric** explicitly scoring (a) retrieval relevance and (b) response correctness separately, plus reporting "Unknown" and "Contradictory" outcomes as first-class categories | Makes "audit-ready" measurable. Without this, the core thesis claim is branding. | YES |
| 3 | **Add a risk audit table** to the report: ~10 rows covering hallucination risk, citation fabrication, contradiction suppression, abstention failure, stale policy, adversarial prompts, etc. | Low effort, high signal. Directly supports "audit-ready" identity. | YES — 2 hours of work, high return |
| 4 | **Create one "objective slice" evaluation** — select 20-30 golden-set queries where the answer has a deterministically checkable structure (specific clause ID, yes/no obligation) | Eliminates "but how do you know the LLM judge is right?" criticism | YES — even 20 questions help |
| 5 | **Add stepwise progression table** showing retrieval metrics → post-reranking metrics → post-verification metrics → final output quality per baseline | Makes the pipeline scientifically legible. Shows each stage adds value. | YES |

### Medium impact — do if time permits

| # | Exact change | Why it matters | Still worth it? |
|---|-------------|---------------|----------------|
| 6 | **Token/cost/latency table** per configuration in the evaluation chapter | Real-world thinking for compliance contexts | YES — data is already in run manifests |
| 7 | **"Use of AI in Thesis" disclosure** — 1 page appendix documenting tools used, what they did, what the student authored | Increasingly expected, avoids ethics friction | YES — 30 minutes |
| 8 | **Evidence rail screenshot pack** — 4-5 screenshots showing: normal evidence, abstention, contradiction, critic mode, reviewer mode | Every major UI claim needs visual proof in the report | YES |
| 9 | **Noisy/adversarial query tests** — run 10-15 deliberately malformed or adversarial queries and document system behaviour | Shows deployment-awareness | Maybe — only if core evaluation is solid |

### Polish-only — last priority

| # | Exact change | Why it matters | Still worth it? |
|---|-------------|---------------|----------------|
| 10 | **Three scripted demo journeys** for viva: happy path, abstention trigger, contradiction trigger | Viva preparation | After everything else |
| 11 | **Consistent iconography** in UI for cited/uncited/contradiction/abstained states | Visual polish | Only if time |

---

## 10. BRUTAL FINAL JUDGEMENT

### Is my project already above most similar student projects?

**Yes.** On system scope, Policy Copilot exceeds every comparator except possibly C1 (Oxford) and C2 (AUEB regulatory). The combination of citation enforcement + abstention + contradiction handling + critic mode + audit export + reviewer mode + experiment explorer + 186-test harness + 105-source research pack is not matched by any single student project in this benchmark set.

Most student RAG dissertations (C5-C9, C13) are evaluation-focused comparison studies with no product UI, no audit export, no reproducibility harness, and no reviewer workflow. Policy Copilot is in a different category.

### What would still stop it from looking elite?

Three things, demonstrated by the strongest comparators:

1. **If "audit-ready" is not measurable** (no failure-mode taxonomy, no two-axis rubric, no evidence-faithfulness metrics), examiners can dismiss the core claim as marketing. C1 and C2 show how to make it measurable.

2. **If evaluation lacks diagnostic depth** — just showing aggregate numbers without per-module failure attribution, stepwise progression, or an objective slice will look like a demo, not research.

3. **If the report doesn't match the codebase** — the codebase is strong, but the dissertation must make the examiner *see* the strength. That means risk audit table, figure density, appendix discipline, requirements → evidence mapping.

### Last few additions most likely to improve your odds

If you can only do a small number of things:

1. **Failure-mode taxonomy + two-axis rubric** in the evaluation chapter (items #1 and #2 above). This is the single highest-impact change.
2. **Risk audit table** in the report (item #3). 2 hours, outsized return.
3. **Stepwise progression table** (item #5). Shows the pipeline is doing real work at each stage.
4. **One objective slice** (item #4). Even 20 deterministically-checkable queries immunise against the "LLM judging itself" criticism.
5. **Screenshot pack** (item #8). Visual proof of every major UI/feature claim.

These five changes would move Policy Copilot from "strong dissertation codebase" to "the examiner has to work hard to find weaknesses."
