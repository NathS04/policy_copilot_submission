#!/usr/bin/env bash
# Phase 6 acceptance tests. Run from repo root. All steps must pass.
set -e
cd "$(dirname "$0")/.."

echo "=== 1) Clean core install (NO ML) ==="
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip -q
pip install -e . -q
python -c "import policy_copilot; print('import ok')"

echo "=== 2) Dev deps + tests ==="
pip install -e ".[dev]" -q
pytest -q

echo "=== 3) CLI help must not crash (lazy imports) ==="
python scripts/run_eval.py --help
python scripts/build_index.py --help

echo "=== 4) Offline reproduction (no keys, no torch) ==="
python scripts/reproduce_offline.py

echo "=== 5) Confirm runs exist and contain real content ==="
ls results/runs/*b2*test*extractive*bm25*/outputs.jsonl
ls results/runs/*b3*test*extractive*bm25*/outputs.jsonl

echo "=== 6) Verify B2 is NOT LLM_DISABLED everywhere ==="
python - <<'PY'
import glob, json
paths = sorted(glob.glob("results/runs/*b2*test*extractive*bm25*/outputs.jsonl"))
assert paths, "missing b2 outputs"
p = paths[-1]
bad=0; good=0
with open(p) as f:
  for line in f:
    r=json.loads(line)
    if r.get("is_answerable")==True:
      if r.get("answer")=="LLM_DISABLED": bad+=1
      elif r.get("answer") not in ("INSUFFICIENT_EVIDENCE","ERROR",None): good+=1
print("answerable_good",good,"answerable_bad_LLM_DISABLED",bad,"file",p)
assert bad==0, "B2 still emits LLM_DISABLED for answerable queries"
assert good>0, "B2 produced no real answers"
PY

echo "=== 7) Strict figures: MUST FAIL if required B1 runs missing ==="
if python eval/analysis/make_figures.py --strict 2>/dev/null; then
  echo "ERROR: strict mode should have failed (B1 missing)"
  exit 1
fi
echo "Strict correctly failed (exit 1)."

echo "=== 8) Non-strict figures: MUST SUCCEED and write to results/ ==="
python eval/analysis/make_figures.py --out_fig_dir results/figures --out_table_dir results/tables

echo "=== 9) Artifact verification: MUST PASS ==="
python scripts/verify_artifacts.py

echo "=== All acceptance tests passed. ==="
