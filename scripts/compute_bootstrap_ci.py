#!/usr/bin/env python3
"""Recompute bootstrap 95% CIs for B3-Generative headline metrics.

Mirrors the per-query computation that ``scripts/run_eval.py`` uses, then
bootstraps each metric on its own denominator (seed=42, n_resamples=2000).

Source artefacts:
- ``results/runs/b3_generative_bm25_fallback_final/outputs.jsonl`` — has
  ``gold_paragraph_ids``, ``evidence``, ``is_abstained``, ``category``.
- ``eval/golden_set/golden_set.csv`` — used only as a sanity check on
  category counts.

Metrics (matching ``scripts/run_eval.py`` lines 470-540):
- ``answer_rate`` = of 36 answerable queries, fraction NOT abstained.
  Reproduces the run's 25.0% point estimate (9/36).
- ``abstention_accuracy`` (the report's "Abstention Accuracy") = of 17
  unanswerable queries, fraction abstained. Reproduces 16/17 = 94.1%.
- ``evidence_recall_at_5`` = mean of per-query
  ``calculate_recall_at_k(retrieved, gold, 5)`` over the 46 queries with
  non-empty ``gold_paragraph_ids`` (36 answerable + 10 contradiction).
  Reproduces the run's 73.9%.

Output: ``results/tables/statistical_confidence.csv``.
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_DIR = ROOT / "results/runs/b3_generative_bm25_fallback_final"
GOLD_CSV = ROOT / "eval/golden_set/golden_set.csv"
OUT_CSV = ROOT / "results/tables/statistical_confidence.csv"

SEED = 42
N_RESAMPLES = 2000


def load_predictions() -> list[dict]:
    out = []
    with (RUN_DIR / "outputs.jsonl").open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_gold_categories() -> dict[str, str]:
    out = {}
    with GOLD_CSV.open() as f:
        for row in csv.DictReader(f):
            out[row["query_id"]] = row["category"]
    return out


def recall_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int = 5) -> float:
    """Mirror eval.metrics.citation_metrics.calculate_recall_at_k (no rounding)."""
    if not gold_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    found = sum(1 for g in gold_ids if g in top_k)
    return found / len(gold_ids)


def bootstrap_ci(values: list[float], seed: int = SEED, n_resamples: int = N_RESAMPLES) -> tuple[float, float, float]:
    """Return (point, lo, hi) for the mean of `values`."""
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    n = len(values)
    point = sum(values) / n
    means = []
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * n_resamples)]
    hi = means[int(0.975 * n_resamples) - 1]
    return (point, lo, hi)


def main() -> int:
    preds = load_predictions()
    gold_cat = load_gold_categories()
    assert len(gold_cat) == 63, f"Expected 63 golden queries, got {len(gold_cat)}"

    answerable = [r for r in preds if r.get("category") == "answerable"]
    unanswerable = [r for r in preds if r.get("category") == "unanswerable"]
    assert len(answerable) == 36, f"answerable {len(answerable)} != 36"
    assert len(unanswerable) == 17, f"unanswerable {len(unanswerable)} != 17"

    # Answer Rate = of 36 answerable, fraction NOT abstained.
    ar_vals = [float(not r.get("is_abstained", False)) for r in answerable]

    # Abstention Accuracy (report sense) = of 17 unanswerable, fraction abstained.
    aa_vals = [float(r.get("is_abstained", False)) for r in unanswerable]

    # Evidence Recall@5: mirror run_eval.py — only queries with non-empty
    # gold_paragraph_ids (comma-separated), no-rounding recall@5.
    er_vals = []
    for r in preds:
        gold_raw = r.get("gold_paragraph_ids", "")
        if not gold_raw or str(gold_raw).lower() == "nan":
            continue
        gold_ids = [x.strip() for x in gold_raw.split(",") if x.strip()]
        retrieved = [e.get("paragraph_id", "") for e in r.get("evidence", [])]
        er_vals.append(recall_at_k(retrieved, gold_ids, 5))

    ar_point, ar_lo, ar_hi = bootstrap_ci(ar_vals)
    aa_point, aa_lo, aa_hi = bootstrap_ci(aa_vals)
    er_point, er_lo, er_hi = bootstrap_ci(er_vals)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "metric", "denominator_n", "point_estimate",
            "ci95_lo", "ci95_hi", "n_resamples", "seed",
        ])
        w.writerow([
            "answer_rate (B3-Gen, 36 answerable)", len(ar_vals),
            f"{ar_point:.4f}", f"{ar_lo:.4f}", f"{ar_hi:.4f}",
            N_RESAMPLES, SEED,
        ])
        w.writerow([
            "abstention_accuracy (B3-Gen, 17 unanswerable)", len(aa_vals),
            f"{aa_point:.4f}", f"{aa_lo:.4f}", f"{aa_hi:.4f}",
            N_RESAMPLES, SEED,
        ])
        w.writerow([
            "evidence_recall_at_5 (B3-Gen, 46 queries with non-empty gold)", len(er_vals),
            f"{er_point:.4f}", f"{er_lo:.4f}", f"{er_hi:.4f}",
            N_RESAMPLES, SEED,
        ])

    pp = lambda x: f"{x*100:.1f}%"  # noqa
    print("Bootstrap 95% CIs (seed=42, n_resamples=2000)")
    print(f"  Answer Rate (36 answerable):                          {pp(ar_point)}  CI [{pp(ar_lo)}, {pp(ar_hi)}]")
    print(f"  Abstention Accuracy (17 unanswerable):                {pp(aa_point)}  CI [{pp(aa_lo)}, {pp(aa_hi)}]")
    print(f"  Evidence Recall@5 (46 queries with non-empty gold):   {pp(er_point)}  CI [{pp(er_lo)}, {pp(er_hi)}]")
    print(f"Wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
