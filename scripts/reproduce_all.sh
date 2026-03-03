#!/usr/bin/env bash
# reproduce_all.sh — One-command reproducibility pack for Policy Copilot
#
# Usage:
#   chmod +x scripts/reproduce_all.sh
#   ./scripts/reproduce_all.sh
#
# Prerequisites:
#   - Python 3.10+ with venv
#   - .env file with OPENAI_API_KEY (for generative runs only)
#   - Raw PDFs in data/corpus/raw/ (provided in submission)
#
# This script runs the full evaluation pipeline from scratch.
# Offline (extractive) runs complete without an API key.
# Generative runs require a funded OpenAI account.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== Policy Copilot — Full Reproduction ==="
echo "Working directory: $(pwd)"
echo ""

# ---- Step 1: Environment ----
echo "[1/7] Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

# ---- Step 2: Ingest corpus ----
echo "[2/7] Ingesting corpus PDFs..."
python -m policy_copilot.ingest.pdf_extract

# ---- Step 3: Build index ----
echo "[3/7] Building FAISS index..."
python -m policy_copilot.index.faiss_index

# ---- Step 4: Run tests ----
echo "[4/7] Running test suite..."
pytest tests/ -x -q --tb=short 2>&1 | tail -5

# ---- Step 5: Offline (extractive) evaluation ----
echo "[5/7] Running extractive baselines (no API key required)..."
python scripts/run_eval.py --baseline b2 --mode extractive --run_name reproduce_b2_extractive
python scripts/run_eval.py --baseline b3 --mode extractive --run_name reproduce_b3_extractive

# ---- Step 6: Online (generative) evaluation ----
echo "[6/7] Running generative baselines (requires OPENAI_API_KEY)..."
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "  ⚠ OPENAI_API_KEY not set — skipping generative runs."
    echo "  Set it in .env or export it to run generative baselines."
else
    python scripts/run_eval.py --baseline b1 --run_name reproduce_b1_generative
    python scripts/run_eval.py --baseline b2 --run_name reproduce_b2_generative
    python scripts/run_eval.py --baseline b3 --run_name reproduce_b3_generative
fi

# ---- Step 7: Generate figures ----
echo "[7/7] Generating figures and tables..."
python eval/analysis/make_figures.py \
    --out_fig_dir docs/report/figures \
    --out_table_dir results/tables

echo ""
echo "=== Reproduction complete ==="
echo "Results: results/runs/"
echo "Figures: docs/report/figures/"
echo "Tables:  results/tables/run_summary.csv"
