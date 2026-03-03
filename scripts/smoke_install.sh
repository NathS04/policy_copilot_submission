#!/usr/bin/env bash
#
# Smoke test: proves the codebase works from a fresh install.
# Run from the repository root.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$(mktemp -d)/smoke_venv"

cleanup() { rm -rf "$(dirname "$VENV_DIR")"; }
trap cleanup EXIT

echo "=== 1/8  Creating fresh venv ==="
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "=== 2/8  Installing core package ==="
pip install -q -e "$REPO_ROOT"

echo "=== 3/8  Verifying package import ==="
python -c "import policy_copilot; print(f'policy_copilot {policy_copilot.__version__} OK')"

echo "=== 4/8  Installing dev extras ==="
pip install -q -e "$REPO_ROOT[dev]"

echo "=== 5/8  Running test suite ==="
cd "$REPO_ROOT"
pytest -q --tb=line --ignore=tests/test_run_eval_requires_key_in_generative.py

echo "=== 6/8  Checking run_eval.py --help ==="
python scripts/run_eval.py --help > /dev/null

echo "=== 7/8  Running offline reproduction ==="
python scripts/reproduce_offline.py

echo "=== 8/8  Running artifact verification ==="
python scripts/verify_artifacts.py

echo ""
echo "============================================="
echo "  SMOKE TEST PASSED — all 8 checks clean"
echo "============================================="
