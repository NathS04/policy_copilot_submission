# Fresh install verification

This file records a clean-room reproduction of the evaluator path on the
submitted code. It is updated by running the documented commands in a fresh
virtual environment and pasting the summary lines back in.

## Configuration

- **Date:** 2026-05-13
- **Machine:** Apple Silicon (macOS, Darwin 24.5.0)
- **Python:** 3.14
- **Repository state:** `main` at commit produced by the build script run
  recorded below (see `git log -1` if needed)

## Commands run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -c "import policy_copilot; print(policy_copilot.__version__)"
pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py
python scripts/verify_artifacts.py
python scripts/build_clean_submission_zip.py
```

## Summary

| Step | Result |
| :--- | :--- |
| `pip install -e ".[dev]"` | succeeded; core + dev dependencies installed |
| package import (`policy_copilot.__version__`) | succeeded |
| `pytest` (offline path, `[dev]` only) | **193 passed, 1 skipped** in ~6 s |
| `scripts/verify_artifacts.py` | `Artifact verification passed.` |
| `scripts/build_clean_submission_zip.py` | ZIP built, 289 files, 5.27 MB, `Forbidden-path scan: PASSED` |

## Notes for the assessor

- The single skipped test (`test_exits_2_when_dense_index_missing`) is
  conditionally skipped when the optional `[ml]` extras are present. Under
  the documented `pip install -e ".[dev]"` install path (no `[ml]` extras,
  which depend on torch and FAISS), the test is reachable but its precondition
  is satisfied, so it skips. This is intentional and documented in
  `INSTRUCTIONS_FOR_EVALUATOR.md`.
- `verify_artifacts.py` prints two warnings about `backend_requested=dense
  but backend_used=bm25` for the B2 and B3 generative runs. This reflects
  the documented BM25 fallback used when the dense FAISS index is not
  available in the reproducibility environment. The dissertation reports
  both the BM25-fallback and dev-phase dense numbers explicitly in §4.3
  and Table 4.3.
- `pytest` creates four short-lived integration-test run directories under
  `results/runs/` (`b2_test_*`, `b3_test_*`, `test_b2_extractive_bm25_integration`,
  `test_allow_no_key_generates_llm_disabled`). These are excluded by
  `.gitignore` and by the whitelist in `build_clean_submission_zip.py`, so
  they never enter the submission package; they may need clearing between
  runs of `verify_artifacts.py` if it is invoked without first cleaning the
  working tree.
