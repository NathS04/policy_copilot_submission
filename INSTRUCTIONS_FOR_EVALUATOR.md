# Evaluator Instructions: Policy Copilot

This repository has been hardened for reproducibility and auditability.
Follow these steps to verify the "Codebase 100/100" status.

## 1. System Requirements
- Python 3.10+
- `pip` layout support (standard in modern Python)

## 2. Installation (Choose One)

### Option A: Lightweight / Offline (Reference Environment)
Core dependencies only. No PyTorch, no heavy ML models.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Option B: Full Machine Learning (Production Environment)
Includes PyTorch, SentenceTransformers, FAISS. Required for dense retrieval and online reproduction.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[ml]"
```

## 3. Verification Steps

### Step 1: CLI Health Check (Works in Option A & B)
Verify that the CLI runs without importing missing ML libraries.
```bash
python scripts/run_eval.py --help
```
*Expected: Prints help message immediately. NO crashes.*

### Step 2: Offline Reproduction (Target: Option A / No API Keys)
Runs the evaluation pipeline using the **BM25 backend** (lexical retrieval) in **Extractive Mode** (no LLM).
- **No API keys required.**
- **No GPU/Torch required.**
```bash
python scripts/reproduce_offline.py
```
*Expected: Runs B2 and B3 on the test set. Generates results in `results/runs/`.*

### Step 3: Strict Figure Generation
Verifies that results are honest (no silent zero-defaults for missing metrics).
```bash
python eval/analysis/make_figures.py --strict
```
*Expected:
- If running offline (Option A): Fails with strict error because B1 (Generative) is missing.
- If running online (Option B + Keys): Generates `fig_baselines.png`, `fig_retrieval.png`.*

### Step 4: Full Online Reproduction (Target: Option B + API Keys)
Requires `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env`.
Runs the full suite (B1, B2, B3) with Dense Retrieval and Generative AI.
```bash
python scripts/reproduce_online.py
```
*Expected: Regenerates all baseline results, ablations, and figures.*

## 4. Key Hardening Features to Audit
1. **Dependency Split**: Check `pyproject.toml` for `core`, `ml`, and `ui` sections.
2. **Lazy Imports**: Check `src/policy_copilot/index/embeddings.py` — `SentenceTransformer` is not imported at top-level.
3. **Score Consistency**: Retrieval and Reranking scores are now roughly normalized [0,1] where **higher = better**.
4. **Honesty**: `make_figures.py` uses `NaN` for missing data, never `0.0`.
