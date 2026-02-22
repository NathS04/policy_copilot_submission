#!/usr/bin/env python3
"""
Selects the best hyperparameter configuration from dev tuning runs.
Reads results/runs/dev_tune_*/summary.json and ranks by a composite score.
Outputs the best config to configs/final_config.json.
"""
import argparse
import json
import sys
from pathlib import Path


def _score(summary: dict) -> float:
    """Composite scoring rule: weighted sum of key metrics.
    Higher is better.
    """
    answer_rate = summary.get("answer_rate", 0) or 0
    abstain_acc = summary.get("abstention_accuracy", 0) or 0
    support_mean = summary.get("support_rate_mean", 0) or 0

    # Weights: abstain accuracy most important (we want reliable silence),
    # then support rate (grounding quality), then answer rate (coverage).
    return 0.4 * abstain_acc + 0.35 * support_mean + 0.25 * answer_rate


def main():
    parser = argparse.ArgumentParser(description="Select best config from dev tuning runs.")
    parser.add_argument("--runs_dir", default="results/runs",
                        help="Directory containing run folders")
    parser.add_argument("--output", default="configs/final_config.json",
                        help="Path to write best config")
    parser.add_argument("--prefix", default="dev_tune_",
                        help="Prefix filter for tuning runs")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    candidates = []

    for run_path in sorted(runs_dir.iterdir()):
        if not run_path.name.startswith(args.prefix):
            continue
        summary_path = run_path / "summary.json"
        config_path = run_path / "run_config.json"
        if not summary_path.exists():
            continue

        with open(summary_path) as f:
            summary = json.load(f)
        cfg = {}
        if config_path.exists():
            with open(config_path) as f:
                cfg = json.load(f)

        score = _score(summary)
        candidates.append({
            "run_name": run_path.name,
            "score": score,
            "summary": summary,
            "config": cfg,
        })

    if not candidates:
        print(f"[!] No tuning runs found matching '{args.prefix}*' in {runs_dir}")
        sys.exit(1)

    # Sort by score descending
    candidates.sort(key=lambda c: -c["score"])

    print(f"{'Rank':<5} {'Run Name':<30} {'Score':<8} {'Abstain%':<10} {'Support%':<10} {'Answer%':<10}")
    print("-" * 73)
    for i, c in enumerate(candidates, 1):
        s = c["summary"]
        print(f"{i:<5} {c['run_name']:<30} {c['score']:<8.4f} "
              f"{s.get('abstention_accuracy', 0) or 0:<10.4f} "
              f"{s.get('support_rate_mean', 0) or 0:<10.4f} "
              f"{s.get('answer_rate', 0) or 0:<10.4f}")

    best = candidates[0]
    print(f"\n[✓] Best: {best['run_name']} (score={best['score']:.4f})")

    # Write best config
    best_cfg = best["config"]
    # Extract the tunable parts
    final = {
        "abstain_threshold": best_cfg.get("abstain_threshold", 0.30),
        "min_support_rate": best_cfg.get("min_support_rate", 0.80),
        "retrieve_k_candidates": best_cfg.get("retrieve_k_candidates", 20),
        "rerank_k_final": best_cfg.get("rerank_k_final", 5),
        "enable_llm_verify": best_cfg.get("enable_llm_verify", False),
        "enable_llm_contradictions": best_cfg.get("enable_llm_contradictions", False),
        "contradiction_policy": best_cfg.get("contradiction_policy", "surface"),
        "provider": best_cfg.get("provider", "openai"),
        "model_name": best_cfg.get("model", "gpt-4o-mini"),
        "temperature": best_cfg.get("temperature", 0.0),
        "seed": best_cfg.get("seed", 42),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(final, f, indent=2)
    print(f"[✓] Saved best config to {out_path}")


if __name__ == "__main__":
    main()
