# Policy Copilot

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/NathS04/policy_copilot_submission/actions/workflows/ci.yml/badge.svg)](https://github.com/NathS04/policy_copilot_submission/actions/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

**Audit-ready Retrieval-Augmented Generation system for policy documents, designed around a *cited-or-silent* rule, abstention, citation verification, contradiction handling, and reproducible reliability evaluation.**

This repository accompanies the COMP3931 dissertation *"Audit-Ready Policy Copilot: Evidence-Grounded Retrieval-Augmented Generation with Deterministic Reliability Controls"* (BSc Computer Science, University of Leeds, 2025/26).

---

## What it does

A user asks a question about a policy document. Policy Copilot:

1. Splits ingested PDFs into paragraphs with stable identifiers.
2. Retrieves relevant paragraphs (dense or BM25) and reranks them with a cross-encoder.
3. Refuses to answer (`INSUFFICIENT_EVIDENCE`) when reranker confidence is below threshold.
4. If confident enough, generates an answer that cites paragraph IDs.
5. Verifies each generated claim against its cited paragraph using token overlap, and prunes any claim the citation does not support.
6. Surfaces contradictions across cited paragraphs.
7. Falls back to **Extractive Mode** (returning the top-ranked paragraph verbatim) when the LLM is unavailable or its output cannot be made citation-clean.
8. Exports a structured audit trail for every query.

The system runs end-to-end on a normal laptop using BM25 + Extractive Mode, or with full dense retrieval + LLM generation when an API key is available.

## Why this project exists

Standard RAG retrieves context and asks a language model to answer; it provides no guarantee that the answer actually uses the retrieved evidence, and gives the model no way to express *I do not know*. In a compliance setting, that is the wrong default: a confidently wrong answer to a policy question can cause real downstream harm. The contribution is not the invention of RAG, but the design and evaluation of a closed-corpus policy QA pipeline where grounding, abstention, citation verification, contradiction handling, and audit export are core requirements rather than optional extras.

## Key features

- PDF ingestion with stable paragraph IDs (`docId::pageId::paraId::contentHash`).
- Dense bi-encoder retrieval, BM25 fallback, and a hybrid mode.
- Cross-encoder reranking (ms-marco-MiniLM-L-6-v2).
- Confidence-gated abstention (per-query).
- Per-claim citation verification using deterministic Jaccard token overlap.
- Numeric / list-style consistency checks.
- Cross-document contradiction detection.
- Extractive Fallback Mode (no LLM, citation precision 100% by construction).
- Heuristic Critic Mode for vague quantifiers, implicit contradictions, and ambiguous directives.
- Streamlit audit workbench (six modes — see *Running the app* below).
- Audit export packets (per-query JSONL with retrieved paragraphs, reranker scores, claim verification, contradictions, latency).
- Reproducible offline evaluation harness.
- 63-query synthetic golden set (44 test, 19 dev).
- Independent peer-reviewer evaluation with Krippendorff's α (Round 2).
- Public Guidance Transfer Stress Test (NCSC + ICO + ACAS, OGL v3.0).
- Adversarial / prompt-injection probe (extractive arm executed; generative pending API quota).
- Examiner-facing evidence pack under `docs/evidence/`.

## Repository map

| Path | Purpose |
| :--- | :--- |
| `src/policy_copilot/` | Production source: ingest, index, retrieve, rerank, generate, verify, critic, service, ui |
| `tests/` | Test suite (193 passed, 1 skipped on the offline path) |
| `scripts/` | CLI entry points (eval runner, reproducibility, figure / report generation) |
| `data/corpus/` | Synthetic policy PDFs and processed paragraphs (project data, not report prose) |
| `data/public_transfer_corpus/` | OGL v3.0 public-guidance corpus + provenance.csv used by §4.11 |
| `eval/golden_set/` | 63-query synthetic golden set with paragraph-level gold IDs |
| `eval/human_eval/` | Independent reviewer evaluation: rubric, consent, P1-P6 aggregate + R1-R6 per-query data |
| `eval/public_transfer/` | Public-transfer failure taxonomy CSV |
| `eval/adversarial/` | 15-query adversarial probe + paired extractive/generative results |
| `eval/results/` | Cached per-run summary tables |
| `results/runs/` | Per-run `outputs.jsonl` + `summary.json` for every reported baseline |
| `results/figures/` | Strict figure outputs that back Chapter 4 |
| `results/tables/` | Aggregate metric tables consumed by the report |
| `docs/report/` | Report markdown source, intermediate DOCX, final PDF |
| `docs/evidence/` | Examiner-facing proof pack: human-eval, public-transfer failure taxonomy, adversarial summary, audit-export examples |
| `docs/research/` | Literature matrix and gap-analysis artefacts |
| `INSTRUCTIONS_FOR_EVALUATOR.md` | Shortest reproduction path for a marker |
| `CHANGELOG.md`, `CONTRIBUTING.md` | Project metadata |

## Quick start

```bash
git clone https://github.com/NathS04/policy_copilot_submission.git
cd policy_copilot_submission

python3 -m venv .venv
source .venv/bin/activate

# Choose tier
pip install -e ".[dev]"        # core + pytest + ruff + mypy (default for evaluators)
# pip install -e ".[ml,dev]"    # + PyTorch, FAISS, SentenceTransformers (dense retrieval)
# pip install -e ".[ui,dev]"    # + Streamlit, Jinja2, Plotly (audit workbench)
# pip install -e ".[llm]"       # + OpenAI, Anthropic clients (generative mode)

python -c "import policy_copilot; print(policy_copilot.__version__)"
pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py
python scripts/reproduce_offline.py
python scripts/verify_artifacts.py
```

The four commands above import the package, run the offline test suite, reproduce the offline evaluation artefacts, and verify the submitted outputs without manual patching. Together they're the main reproducibility check for this submission.

## Running the app

```bash
pip install -e ".[ui,llm,dev]"
streamlit run src/policy_copilot/ui/streamlit_app.py
```

The audit workbench has **six modes**:

1. **Ask** — submit a query and view the answer with cited evidence and verification badges.
2. **Audit Trace** — full per-query audit trail (retrieval, rerank, abstention gate, claim verification, contradictions, latency).
3. **Critic Lens** — applies the Critic Mode heuristics to user-supplied policy text.
4. **Experiment Explorer** — compare runs side-by-side across baselines and ablations.
5. **Reviewer Mode** — paginated rubric scoring view used by the human evaluation in §4.10.
6. **Help & Guide** — in-app reference for the rubric, the abstention thresholds, and the audit fields.

## Reproducing evaluation results

The default reproduction path is **offline / no API key** and uses the BM25 retrieval backend.

```bash
python scripts/run_eval.py --baseline b3 --mode extractive   # B3-Extractive (no LLM)
python scripts/reproduce_offline.py                           # B2 + B3 extractive over the test split
python scripts/verify_artifacts.py                            # provenance + orphan-table check
```

The full **online / generative** path requires an API key and may incur cost:

```bash
export OPENAI_API_KEY="..."
python scripts/run_eval.py --baseline b3 --mode generative
python scripts/reproduce_online.py
```

The final retrieval reported in the dissertation used the **BM25 fallback** because the dense FAISS index was unavailable in the reproducibility environment; the dense / development numbers are reported separately in §4.13.

## Reported headline results

All values are real; caveats are stated next to each metric.

| Metric | Result | Caveat |
| :--- | :--- | :--- |
| B3-Generative response-level Ungrounded Rate | **0.0%** | After post-LLM `min_support_rate` enforcement (§4.4); not proof the LLM never hallucinates |
| B3-Generative claim-level residual Ungrounded Rate | **4%** | Two-thirds reduction from the 12% pre-verification baseline |
| B3-Generative Abstention Accuracy (test split) | **94.1%** | n = 12 unanswerable test queries; bootstrap CI is wide (§4.12) |
| B3-Generative Answer Rate (test split) | **25.0%** | Below the 85% target; the visible price of the strict "cited or silent" rule |
| B3-Extractive Answer Rate | **89%** | Coverage is broadly recovered |
| B3-Extractive Citation Precision | **100%** | True by construction (the response is the cited paragraph) |
| Public Guidance Transfer Evidence Recall@5 | **52.1%** | Halved from 85% on the synthetic test split (§4.11) |
| Public Guidance Transfer Ungrounded Rate | **0.0%** | On this small extractive-only transfer set, the system stayed conservative and did not fabricate cited answers |
| Critic Mode macro F1 | **84.8%** | Marginally below the 85% target |
| Round 2 Krippendorff's α (per axis) | **0.74 / 0.26 / 0.34 / 0.73 / 0.74** | Three axes in tentative-agreement band; ceiling effect on Groundedness, see Appendix B.10 |
| Independent reviewer evaluation | Correctness 4.67, Groundedness 4.83, Usefulness 3.67 | Round 1 aggregate; n = 6 peer reviewers, author-facilitated |

## Evidence pack

`docs/evidence/` collects the main files an examiner can use to check any claim against an artefact.

| Evidence | Path | Supports |
| :--- | :--- | :--- |
| Contribution map (what is the author's work) | `docs/evidence/contribution_map.md` | Authorship and scope of contribution |
| Fresh-install verification log | `docs/evidence/verification/fresh_install_log.md` | Pytest / verify_artifacts / clean ZIP from a fresh venv |
| Independent reviewer scores (Round 1 + Round 2) | `docs/evidence/human_eval/anonymised_scores.csv`, `per_query_anonymised_scores.csv` | Section 4.10, Appendix B.10, Tables B.3 / B.4 |
| Inter-rater agreement (Krippendorff α + 95% CI) | `docs/evidence/human_eval/inter_rater_agreement.md` | Section 4.10, Appendix B.10 Table B.4 |
| Public Guidance Transfer corpus provenance | `data/public_transfer_corpus/provenance.csv` | Section 4.11, Appendix B.11 Table B.5 |
| Public-transfer failure taxonomy | `eval/public_transfer/failure_taxonomy.csv`, `docs/evidence/verification/public_transfer_failure_taxonomy.md` | Section 4.11 |
| Adversarial probe summary | `eval/adversarial/adversarial_summary.csv`, `docs/evidence/verification/adversarial_test_summary.md` | Appendix B.12 Table B.6 |
| Audit-export examples (3 cases) | `docs/evidence/verification/audit_export_*.md` | The "audit-ready" claim, made visible |
| Final report PDF | `docs/report/Final_Report_Nathaniel_Sebastian_201715051.pdf` | The dissertation itself |
| Reproducibility checklist | `docs/evidence/checklist.md` | Per-claim mapping of report → artefact |
| Capture guide | `docs/evidence/capture_guide.md` | How each artefact was produced and how to regenerate it |

## Reproducibility

The repo is set up so that a fresh install can import the package, run the offline test suite, reproduce the offline evaluation artefacts, and verify the submitted outputs without any manual patching.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -c "import policy_copilot; print(policy_copilot.__version__)"
pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py
python scripts/reproduce_offline.py
python scripts/verify_artifacts.py
```

If any step fails on a reasonable environment (Python 3.10+, macOS / Linux, ~1 GB free disk for index files), it is a reproducibility regression — please raise an issue describing the OS and the failing step.

## Limitations

- The primary benchmark corpus is synthetic; transfer to noisier real-world documents is partially probed by the Public Guidance Transfer Stress Test but full transfer is not demonstrated.
- The Public Guidance Transfer Stress Test is small (20 queries, 8 documents).
- The independent reviewer evaluation is small (n = 6 across two rounds), author-facilitated rather than fully blinded, and the reviewer pool is non-domain-expert (CS peers, not compliance specialists).
- The generative arm of the adversarial probe (Appendix B.12 / Table B.6) was not executed end-to-end at submission time: the OpenAI account returned `insufficient_quota` (HTTP 429) on every call. The runner is parameterised to complete the paired numbers in a single command on a billing-active account.
- Final retrieval results were obtained on the BM25 backend after the dense FAISS index was unavailable in the reproducibility environment; dense-index development numbers are reported separately.
- The system has not been deployed against a real organisational policy corpus; production deployment would require access control, monitoring, audit-log retention policy, and domain-expert validation.

## AI use and authorship

Generative AI tools were used as disclosed in Appendix B.5 of the report: GitHub Copilot for code autocompletion during specific sprints, ChatGPT (GPT-4 / GPT-4o) for debugging and synthetic corpus generation (project data only, not report prose), and Claude Opus (Anthropic) for writing-review support during report preparation. AI outputs were treated as suggestions or review comments rather than final authoritative text. The final code, report wording, claims, metrics, citations, edits, and submission decisions were reviewed, revised where necessary, and approved by the author. Use was Amber-category (COMP3931 / COMP3932) — assistive, not replacement authorship.

## Licence

- Code: MIT licence — see [LICENSE](LICENSE).
- Public guidance corpus (`data/public_transfer_corpus/`): Open Government Licence v3.0; provenance and content hashes recorded in `data/public_transfer_corpus/provenance.csv`.
- Synthetic policy corpus (`data/corpus/`): authored for this project; project data, not third-party content.
- Reviewer evaluation materials (`eval/human_eval/` and `docs/evidence/human_eval/`): anonymised at collection time, used only for the dissertation's Section 4.10 and Appendix B.10.

## Citation

```bibtex
@misc{sebastian2026policycopilot,
  author = {Sebastian, Nathaniel},
  title  = {Policy Copilot: Audit-Ready Retrieval-Augmented Generation with Deterministic Reliability Controls},
  year   = {2026},
  note   = {BSc Computer Science Individual Project, University of Leeds (COMP3931)}
}
```
