# Policy Copilot

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/NathS04/policy_copilot_submission/actions/workflows/ci.yml/badge.svg)](https://github.com/NathS04/policy_copilot_submission/actions/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://docs.astral.sh/ruff/)

**Audit-Ready RAG with Citation Enforcement and Reliability Evaluation**

> A retrieval-augmented generation system that answers questions over policy documents
> only when it can cite specific supporting paragraphs — *cited or silent*.
> Built as a COMP3931 dissertation project at the University of Leeds.

---

## Motivation

Standard RAG pipelines retrieve context and generate answers, but they provide no
guarantees about whether the answer is actually grounded in the retrieved evidence.
Policy Copilot adds a **reliability layer** on top of RAG: confidence-gated abstention,
per-claim citation verification, contradiction detection, and a critic mode that flags
problematic policy language. Every answer carries a full audit trail.

## Key Features

| Feature | Description |
|---|---|
| **Confidence-gated abstention** | Abstains when retrieval confidence is too low to answer reliably |
| **Per-claim citation verification** | Splits answers into claims and verifies each against cited evidence |
| **Contradiction detection** | Surfaces conflicting evidence across retrieved paragraphs |
| **Critic mode (L1–L6)** | Detects normative language, framing bias, unsupported claims, internal contradictions, false dilemmas, and slippery-slope reasoning |
| **Audit trail export** | JSON/HTML audit reports with full provenance metadata |
| **Interactive workbench** | 5-mode Streamlit UI: Ask, Audit Trace, Critic Lens, Experiment Explorer, Reviewer Mode |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Workbench                      │
│   Ask │ Audit Trace │ Critic Lens │ Experiments │ Reviewer      │
├─────────────────────────────────────────────────────────────────┤
│                      Service / Orchestrator                     │
│   ChatOrchestrator · AuditReportService · ReviewerService       │
├──────────┬──────────┬───────────┬───────────┬──────────────────┤
│ Retrieve │ Rerank   │ Generate  │ Verify    │ Critic           │
│ BM25     │ Cross-   │ LLM with  │ Claim     │ L1-L6 heuristic  │
│ Dense    │ encoder  │ citation  │ split +   │ + LLM detection  │
│ Hybrid   │ scoring  │ enforce   │ check +   │                  │
│          │          │           │ contradict│                  │
└──────────┴──────────┴───────────┴───────────┴──────────────────┘
```

## Baselines

| Baseline | Description |
|---|---|
| **B1** | Prompt-only LLM — no retrieval; measures hallucination baseline |
| **B2** | Naive RAG — top-k=5 evidence, no reranking or abstention |
| **B3** | Full system — reranking + confidence-gated abstention + per-claim citation verification + contradiction surfacing |

## Quick Start

```bash
# Clone and set up
git clone https://github.com/NathS04/policy_copilot_submission.git
cd policy_copilot_submission

# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install (choose tier)
pip install -e .              # Core: BM25, eval, plotting
pip install -e ".[dev]"       # + pytest, ruff, mypy
# pip install -e ".[ml]"     # + PyTorch, FAISS, SentenceTransformers
# pip install -e ".[ui]"     # + Streamlit, Jinja2, Plotly
# pip install -e ".[llm]"    # + OpenAI, Anthropic

# Configure API keys (required for generative mode)
cp .env.example .env          # Then edit .env
```

## Usage

### Evaluation Pipeline

```bash
# Run full system evaluation
python scripts/run_eval.py --baseline b3 --run_name b3_full

# Run all baselines
python scripts/run_eval.py --baseline all --run_name comparison

# Ablation studies
python scripts/run_eval.py --baseline b3 --run_name ablate_no_rerank --no_rerank
python scripts/run_eval.py --baseline b3 --run_name ablate_no_verify --no_verify
```

### Interactive Workbench

```bash
pip install -e ".[ui]"
streamlit run src/policy_copilot/ui/streamlit_app.py
```

### CLI Query

```bash
python scripts/query_cli.py "What is the policy on X?" --llm
```

## Reproducibility

Two reproduction scripts are provided for verifying results:

| Script | Requirements | What it does |
|---|---|---|
| `scripts/reproduce_offline.py` | Core deps only | Runs B2/B3 in extractive mode with BM25. No API keys or GPU needed. |
| `scripts/reproduce_online.py` | ML + LLM deps, API keys | Runs full B1/B2/B3 suite with dense retrieval and LLM generation. |

```bash
# Offline (no API keys, no GPU)
python scripts/reproduce_offline.py

# Online (requires API keys in .env)
python scripts/reproduce_online.py

# Verify artefact integrity
python scripts/verify_artifacts.py
python scripts/verify_artifacts.py --strict
```

See [INSTRUCTIONS_FOR_EVALUATOR.md](INSTRUCTIONS_FOR_EVALUATOR.md) for detailed verification steps.

## Golden Set

63 queries split into 19 dev (threshold tuning) and 44 test (evaluation):

| Category | Count |
|---|---|
| Answerable | 36 |
| Unanswerable | 17 |
| Contradiction probes | 10 |
| **Total** | **63** |

## Evaluation Metrics

| Metric | Definition |
|---|---|
| **Answer rate** | Fraction of queries that produced a non-abstention answer |
| **Abstention accuracy** | Correct abstention rate on unanswerable queries |
| **Ungrounded rate** | Fraction of claims not supported by cited evidence |
| **Citation precision** | Fraction of cited paragraphs that actually support a claim |
| **Critic macro precision** | Average precision across L1–L6 critic categories |

## Project Structure

```
policy_copilot_submission/
├── src/policy_copilot/
│   ├── config.py                 # Pydantic settings
│   ├── ingest/                   # PDF extraction, chunking, paragraph IDs
│   ├── index/                    # FAISS index, embeddings
│   ├── retrieve/                 # BM25, dense, hybrid retrieval
│   ├── rerank/                   # Cross-encoder reranking
│   ├── generate/                 # LLM answer generation with citation enforcement
│   ├── verify/                   # Abstention, claim splitting, citation check, contradictions
│   ├── critic/                   # L1-L6 policy language critic
│   ├── service/                  # Orchestrator, audit reports, reviewer, run inspector
│   └── ui/                       # Streamlit workbench (theme, components, renderers, state)
├── eval/
│   ├── golden_set/               # 63-query golden set with annotations
│   ├── metrics/                  # Evaluation metric implementations
│   ├── runners/                  # Baseline runner harnesses
│   ├── analysis/                 # Figure and table generation
│   └── human_eval/               # Human rubric tooling
├── scripts/                      # CLI scripts for all pipeline stages
├── tests/                        # 38 test modules
├── docs/
│   ├── research/                 # Literature matrix, taxonomy, gap statement
│   └── report/                   # Dissertation report drafts
├── configs/                      # Run configuration files
└── results/                      # Evaluation run outputs and figures
```

## Documentation

| Document | Description |
|---|---|
| [INSTRUCTIONS_FOR_EVALUATOR.md](INSTRUCTIONS_FOR_EVALUATOR.md) | Step-by-step verification guide |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development workflow and conventions |
| [docs/ui_architecture.md](docs/ui_architecture.md) | UI module architecture |
| [docs/claim_evidence_map.md](docs/claim_evidence_map.md) | Mapping of report claims to code evidence |
| [docs/requirements_traceability_matrix.md](docs/requirements_traceability_matrix.md) | Requirements to implementation traceability |
| [docs/reproducibility_checklist.md](docs/reproducibility_checklist.md) | Reproducibility verification checklist |
| [docs/research/](docs/research/) | Literature review artefacts |

## Limitations & Future Work

- **Dense retrieval** requires PyTorch and ~2 GB of model weights; BM25 fallback is always available
- **Human evaluation** tooling is implemented but inter-rater agreement (Cohen's kappa) was not exercised due to single-rater constraints — this remains future work
- **LLM judge verification** (Tier-2) is optional and API-cost-dependent
- **Critic mode** uses heuristic detection with optional LLM augmentation; precision varies by label category

## Citation

If you use this work, please cite:

```bibtex
@dissertation{sebastian2026policycop,
  title   = {Audit-Ready Policy Copilot: RAG with Citation Enforcement
             and Reliability Evaluation},
  author  = {Sebastian, Nathan},
  school  = {University of Leeds},
  year    = {2026},
  type    = {BSc Dissertation (COMP3931)}
}
```

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
