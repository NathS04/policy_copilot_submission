"""Bootstrap CIs over corrected denominators (Phase J).

Parameterised version of ``scripts/compute_bootstrap_ci.py``. Iterates
over the v2 run directories and writes a single CSV with one row per
(run, metric) combination.

Used metrics:
  - answer_rate           (denominator = answerable queries)
  - abstention_accuracy   (denominator = unanswerable queries)
  - evidence_recall_at_5  (denominator = queries with non-empty gold)
  - citation_precision    (denominator = surfaced answerable queries with citations)

Seed=42, n_resamples=2000. Deterministic.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import List, Tuple


ROOT = Path(__file__).resolve().parents[1]
SEED = 42
N_RESAMPLES = 2000

NON_ANSWERS = {"INSUFFICIENT_EVIDENCE", "LLM_DISABLED", "ERROR", ""}

RUNS_TO_COVER = [
    # (run_dir_name, label, baseline)
    ("b1_generative_v2",                          "B1 (replay, v2 corrected)", "b1"),
    ("b2_generative_v2",                          "B2-Generative (replay, v2)", "b2"),
    ("b2_extractive_hybrid_v2_final",             "B2-Extractive hybrid (v2)", "b2"),
    ("b3_generative_v2",                          "B3-Generative (replay, v2)", "b3"),
    ("b3_extractive_hybrid_v2_final",             "B3-Extractive hybrid (v2)", "b3"),
    ("b4_conservative_hybrid_replay_v2_final",    "B4 Conservative Hybrid (v2 replay)", "b4"),
    ("b5_evidence_gated_hybrid_v3_final",         "B5 Evidence-Gated Hybrid (v3)",     "b5"),
]


def load_outputs(p: Path) -> List[dict]:
    out = []
    with p.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def recall_at_k(retrieved: List[str], gold: List[str], k: int = 5) -> float:
    if not gold:
        return 1.0
    top_k = set(retrieved[:k])
    return sum(1 for g in gold if g in top_k) / len(gold)


def bootstrap_ci(values: List[float], seed: int = SEED, n: int = N_RESAMPLES) -> Tuple[float, float, float]:
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    nn = len(values)
    point = sum(values) / nn
    means = []
    for _ in range(n):
        s = [values[rng.randrange(nn)] for _ in range(nn)]
        means.append(sum(s) / nn)
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[int(0.975 * n) - 1]
    return (point, lo, hi)


def compute_for_run(run_dir: Path, baseline: str) -> dict:
    recs = load_outputs(run_dir / "outputs.jsonl")
    answerable = [r for r in recs if r.get("category") == "answerable"]
    unanswerable = [r for r in recs if r.get("category") == "unanswerable"]

    out = {}

    if answerable:
        # answered = answer not in NON_ANSWERS (mirrors run_eval._write_summary_metrics)
        vals = [
            float((r.get("answer") or "").strip() not in NON_ANSWERS
                  and bool((r.get("answer") or "").strip()))
            for r in answerable
        ]
        out["answer_rate"] = (bootstrap_ci(vals), len(vals))

    if unanswerable:
        vals = [float(r.get("is_abstained", False)) for r in unanswerable]
        out["abstention_accuracy"] = (bootstrap_ci(vals), len(vals))

    def _retrieved_ids(r: dict) -> list:
        # Match the fallback pattern used in scripts/run_eval.py:_write_summary_metrics
        if r.get("evidence"):
            return [e.get("paragraph_id", "") for e in r["evidence"]]
        rpi = r.get("retrieved_paragraph_ids")
        if isinstance(rpi, list):
            return rpi
        if isinstance(rpi, str):
            return [x.strip() for x in rpi.split(",") if x.strip()]
        return []

    er_vals = []
    for r in recs:
        gold_raw = (r.get("gold_paragraph_ids") or "").strip()
        if not gold_raw or gold_raw.lower() == "nan":
            continue
        gold_ids = [x.strip() for x in gold_raw.split(",") if x.strip()]
        retrieved = _retrieved_ids(r)
        er_vals.append(recall_at_k(retrieved, gold_ids, 5))
    if er_vals:
        out["evidence_recall_at_5"] = (bootstrap_ci(er_vals), len(er_vals))

    # citation_precision: of answered answerable records, fraction of citations valid.
    cp_vals = []
    for r in answerable:
        ans = (r.get("answer") or "").strip()
        if ans in NON_ANSWERS:
            continue
        cits = r.get("citations") or []
        if isinstance(cits, str):
            cits = [c.strip() for c in cits.split("|") if c.strip()]
        retrieved = _retrieved_ids(r)
        if not cits:
            cp_vals.append(0.0)
            continue
        retr_set = set(retrieved)
        valid = sum(1 for c in cits if c in retr_set)
        cp_vals.append(valid / len(cits))
    if cp_vals:
        out["citation_precision"] = (bootstrap_ci(cp_vals), len(cp_vals))

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-csv", type=Path,
                        default=ROOT / "results/tables/statistical_confidence_v2.csv")
    args = parser.parse_args()

    rows = []
    for run_name, label, baseline in RUNS_TO_COVER:
        run_dir = ROOT / "results/runs" / run_name
        if not run_dir.exists():
            print(f"SKIP {run_name} (not present)")
            continue
        metrics = compute_for_run(run_dir, baseline)
        for metric_name, ((point, lo, hi), n) in metrics.items():
            rows.append({
                "run_name": run_name,
                "label": label,
                "baseline": baseline,
                "metric": metric_name,
                "denominator_n": n,
                "point_estimate": round(point, 4),
                "ci95_lo": round(lo, 4),
                "ci95_hi": round(hi, 4),
                "n_resamples": N_RESAMPLES,
                "seed": SEED,
            })

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {args.out_csv}\n")
    for r in rows:
        print(
            f"  {r['label'][:42]:42s} {r['metric']:>22s}: "
            f"{r['point_estimate']*100:5.1f}%  "
            f"[{r['ci95_lo']*100:5.1f}%, {r['ci95_hi']*100:5.1f}%]  "
            f"n={r['denominator_n']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
