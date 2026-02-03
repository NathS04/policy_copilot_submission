# Instructions for GPT / Evaluator — Run These Exactly

**Unzip the repo, then `cd policy_copilot_submission` and run the following in order. Every step must succeed or the codebase fails Phase 6. Use the same shell (activate venv once and keep it).**

Quick one-shot (after Steps 1–2): `./scripts/run_acceptance_tests.sh` runs steps 4–9; Step 7 must "fail" (exit 1) for strict mode — the script treats that as success.

---

## Step 1: Clean core install (no ML)

```bash
cd policy_copilot_submission
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
python -c "import policy_copilot; print('import ok')"
```

**Expected:** Last line prints `import ok`. No errors.

---

## Step 2: Dev deps and tests

```bash
pip install -e ".[dev]"
pytest -q
```

**Expected:** All tests pass (e.g. `89 passed`). Exit code 0.

---

## Step 3: CLI help must not crash

```bash
python scripts/run_eval.py --help
python scripts/build_index.py --help
```

**Expected:** Help text for both. No import errors, no crash.

---

## Step 4: Offline reproduction (no API keys, no torch)

```bash
python scripts/reproduce_offline.py
```

**Expected:** Runs B2 and B3 (test, extractive, bm25). Creates `results/runs/*b2*.../outputs.jsonl` and `*b3*.../outputs.jsonl`. Ends with `=== OFFLINE REPRODUCTION COMPLETE ===`. Exit code 0.

---

## Step 5: Confirm B2/B3 output files exist

```bash
ls results/runs/*b2*test*extractive*bm25*/outputs.jsonl
ls results/runs/*b3*test*extractive*bm25*/outputs.jsonl
```

**Expected:** At least one path for each. No "No such file".

---

## Step 6: B2 must not be LLM_DISABLED for answerable queries

```bash
python - <<'PY'
import glob, json
paths = sorted(glob.glob("results/runs/*b2*test*extractive*bm25*/outputs.jsonl"))
assert paths, "missing b2 outputs"
p = paths[-1]
bad = good = 0
with open(p) as f:
    for line in f:
        r = json.loads(line)
        if r.get("is_answerable") == True:
            if r.get("answer") == "LLM_DISABLED":
                bad += 1
            elif r.get("answer") not in ("INSUFFICIENT_EVIDENCE", "ERROR", None):
                good += 1
print("answerable_good", good, "answerable_bad_LLM_DISABLED", bad)
assert bad == 0, "B2 still emits LLM_DISABLED for answerable queries"
assert good > 0, "B2 produced no real answers"
PY
```

**Expected:** Prints e.g. `answerable_good 25 answerable_bad_LLM_DISABLED 0`. No assertion error.

---

## Step 7: Strict figures must FAIL (B1 missing in offline)

```bash
python eval/analysis/make_figures.py --strict
```

**Expected:** Exit code **1**. Stderr contains something like `STRICT ERROR: fig_baselines requires runs that are missing: ['b1/test']`. This is correct — strict mode must fail when required B1 runs are missing.

---

## Step 8: Non-strict figures must succeed

```bash
python eval/analysis/make_figures.py --out_fig_dir results/figures --out_table_dir results/tables
```

**Expected:** Exit code 0. Prints "Saved results/figures/fig_*.png" and "Saved results/tables/run_summary.csv".

---

## Step 9: Artifact verification must pass

```bash
python scripts/verify_artifacts.py
```

**Expected:** Exit code 0. Last line: `Artifact verification passed.` Also writes `results/manifest.json`.

---

## Optional: One-shot script

From repo root:

```bash
chmod +x scripts/run_acceptance_tests.sh
./scripts/run_acceptance_tests.sh
```

**Expected:** All steps 1–9 run in sequence and finish with `=== All acceptance tests passed. ===`.  
Note: Step 7 in the script expects strict to fail; the script treats that as success.

---

## If anything fails

- **Step 1 fails:** Check Python is 3.10+ and you are in the repo root.
- **Step 2 fails:** Run `pip install -e ".[dev]"` again; fix any test or import errors reported.
- **Step 4 fails:** Ensure `data/corpus/processed/paragraphs.jsonl` and `eval/golden_set/golden_set.csv` exist (they are in the zip).
- **Step 6 fails:** B2 extractive is broken (allow_fallback not passed or extractive path wrong).
- **Step 7 succeeds (exit 0):** That is wrong — strict must fail when B1 is missing; fix make_figures --strict.
- **Step 9 fails:** Remove any extra files under `results/figures/` or `results/tables/` that are not produced by make_figures (e.g. fig_ablations.png, table_headline_metrics.csv).
