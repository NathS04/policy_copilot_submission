# Fresh install verification

This file records a clean-room reproduction of the evaluator path on the
submitted code. It is updated by running the documented commands in a
fresh virtual environment and pasting the summary lines back in.

## Configuration

- **Date:** 2026-05-13
- **Machine:** Apple Silicon (macOS, Darwin 24.5.0)
- **Python:** 3.14
- **Repository state:** `main` at the commit produced by the build run
  recorded below (run `git log -1` if needed)

## Commands run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -c "import policy_copilot; print(policy_copilot.__version__)"
pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py
python scripts/reproduce_offline.py
python scripts/verify_artifacts.py
python scripts/build_clean_submission_zip.py
```

## Summary

| Step | Result |
| :--- | :--- |
| `pip install -e ".[dev]"` | succeeded; core + dev dependencies installed |
| package import (`policy_copilot.__version__`) | succeeded |
| `pytest` (offline path, `[dev]` only) | **290 passed, 2 skipped** in ~7 s |
| `scripts/reproduce_offline.py` | `=== OFFLINE REPRODUCTION COMPLETE ===` — B2 and B3 re-run on the test split in Extractive Mode, BM25 backend, no API calls |
| `scripts/verify_artifacts.py` | `Artifact verification passed.` |
| `scripts/build_clean_submission_zip.py` | ZIP built, 302 files, ~5.3 MB, `Forbidden-path scan: PASSED`, `ZIP accepted.` |

## Expected notices and intentional behaviours

- The single skipped test (`tests/test_reproduce_online_requires_dense_index.py`,
  `test_exits_2_when_dense_index_missing`) is conditionally skipped: it
  requires the optional `[ml]` extras to be *absent*, which is the
  situation under the documented evaluator install. Under a fuller
  install (with `[ml]`), the test would run and pass instead.
- `verify_artifacts.py` prints two `EXPECTED NOTICE: ... backend_requested=dense
  but backend_used=bm25` lines for `b2_generative_bm25_fallback_final` and
  `b3_generative_bm25_fallback_final`. This is the documented BM25 fallback
  used in the final reproducibility environment; it is discussed in the report
  at §4.3 and §4.13 and is intentional. The notice is retained (rather than
  silenced) so the fallback cannot be mistaken for a silent dense-retrieval
  result. `make_figures.py` may also print equivalent warnings.
- `pytest` creates four short-lived integration-test run directories
  under `results/runs/` (`b2_test_*`, `b3_test_*`,
  `test_b2_extractive_bm25_integration`, and
  `test_allow_no_key_generates_llm_disabled`), and
  `reproduce_offline.py` creates two more (`b2_test_extractive_bm25_*`,
  `b3_test_extractive_bm25_*`) by design when re-running the offline
  reproduction. All of these are excluded by `.gitignore` and by the
  whitelist in `scripts/build_clean_submission_zip.py`, so they never
  enter the submission ZIP. They may be present in a local working
  tree after the offline path runs and can be cleared with
  `rm -rf results/runs/b2_test_* results/runs/b3_test_* results/runs/test_*`.

## Cross-references

- `INSTRUCTIONS_FOR_EVALUATOR.md` — full step-by-step path.
- `docs/evidence/checklist.md` — claim → artefact → command mapping for
  every Chapter 4 headline.
- `docs/evidence/contribution_map.md` — what is the author's own work
  vs third-party components.
