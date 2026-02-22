#!/bin/bash
# run_dev_tuning.sh — Grid search over B3 hyperparameters on DEV split
# Runs 12 combinations: 4 abstain_thresholds × 3 min_support_rates
set -e

PYTHON=".venv/bin/python"
THRESHOLDS=(-3.0 -1.0 1.0 3.0)
SUPPORT_RATES=(0.60 0.80)

echo "=== DEV Tuning Grid Search ==="
echo "Thresholds: ${THRESHOLDS[*]}"
echo "Support rates: ${SUPPORT_RATES[*]}"
echo ""

for t in "${THRESHOLDS[@]}"; do
    for s in "${SUPPORT_RATES[@]}"; do
        # Use simple underscores for run names
        RUN_NAME="dev_tune_t${t}_s${s}"
        echo "[*] Running: $RUN_NAME  (abstain=$t, support=$s)"
        $PYTHON scripts/run_eval.py \
            --baseline b3 \
            --split dev \
            --run_name "$RUN_NAME" \
            --abstain_threshold "$t" \
            --min_support_rate "$s" \
            --force
        echo ""
    done
done

echo "=== Grid search complete ==="
echo "Run: python scripts/select_best_config.py"
