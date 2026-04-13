# Reproducibility Checklist

Step-by-step verification of the project's reproducibility claims.

## Prerequisites

- Python 3.10+
- macOS or Linux
- Internet connection (for online reproduction only)

## Path A: Offline Reproduction (No API Keys, No GPU)

```bash
# 1. Fresh virtual environment
python3 -m venv .venv_test
source .venv_test/bin/activate

# 2. Install core package
pip install -e .
pip install -e ".[dev]"

# 3. Verify import
python -c "import policy_copilot; print(policy_copilot.__version__)"
# Expected: 0.1.0

# 4. Run tests
pytest -q
# Expected: 186 passed, 1 skipped

# 5. CLI health check
python scripts/run_eval.py --help
# Expected: prints help, no crash

# 6. Offline reproduction
python scripts/reproduce_offline.py
# Expected: runs B2 and B3 in extractive mode using BM25

# 7. Strict figure generation (should fail without B1 generative)
python eval/analysis/make_figures.py --strict
# Expected: fails with error about missing B1 data

# 8. Non-strict figure generation
python eval/analysis/make_figures.py
# Expected: generates available figures, NaN for missing
```

## Path B: Online Reproduction (API Keys Required)

```bash
# 1. Set up API keys
cp .env.example .env
# Edit .env: add OPENAI_API_KEY=sk-...

# 2. Install with ML extras
pip install -e ".[ml,llm]"

# 3. Build dense index (if not present)
python scripts/build_index.py

# 4. Full online reproduction
python scripts/reproduce_online.py
# Expected: runs B1, B2, B3 generative with dense retrieval

# 5. Strict figure generation (should succeed)
python eval/analysis/make_figures.py --strict
# Expected: generates fig_baselines.png, fig_retrieval.png, fig_tradeoff.png
```

## Verification Checks

| Check | Command | Expected |
|-------|---------|----------|
| Package imports cleanly | `python -c "import policy_copilot"` | No error |
| Tests pass | `pytest -q` | 186 passed, 1 skipped |
| Golden set valid | `python scripts/validate_golden_set.py` | All checks pass |
| Run artifacts present | `ls results/runs/b3_generative_bm25_fallback_final/summary.json` | File exists |
| Manifest valid | `python scripts/verify_artifacts.py` | All checks pass |

## Known Limitations

- Tests `test_run_eval_requires_key_in_generative.py` may timeout if the system has API keys configured (the test attempts actual LLM calls)
- Dense retrieval requires `pip install -e ".[ml]"` and approximately 2 GB of model downloads on first run
- Online reproduction requires a valid OpenAI API key and incurs API costs
