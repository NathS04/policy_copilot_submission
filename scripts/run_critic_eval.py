#!/usr/bin/env python3
"""
Runs critic evaluation on the labelled snippet dataset.
Computes precision/recall/F1 per label + macro F1.
"""
import argparse
import json
import sys
from pathlib import Path

# ensure project root is on sys.path for eval.metrics imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from policy_copilot.critic.critic_agent import detect
from policy_copilot.critic.labels import LABEL_IDS
from eval.metrics.critic_metrics import compute_critic_metrics


def _load_snippets(base_dir: Path) -> list[dict]:
    """Load all neutral + manipulated snippets."""
    snippets = []
    for subdir in ["neutral", "manipulated"]:
        path = base_dir / subdir / "critic_snippets.jsonl"
        if path.exists():
            with open(path, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        obj["version"] = subdir
                        snippets.append(obj)
                    except json.JSONDecodeError:
                        pass
    return snippets


def main():
    parser = argparse.ArgumentParser(description="Run critic evaluation.")
    parser.add_argument("--run_name", required=True,
                        help="Name for this evaluation run")
    parser.add_argument("--mode", choices=["heuristic", "llm"], default="heuristic",
                        help="Detection mode: heuristic (Tier 1) or llm (Tier 2)")
    parser.add_argument("--data_dir", default="data/handbook/variants",
                        help="Base directory for critic snippets")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    snippets = _load_snippets(data_dir)

    if not snippets:
        print(f"[!] No snippets found in {data_dir}")
        sys.exit(1)

    print(f"[+] Loaded {len(snippets)} snippets ({args.mode} mode)")

    # setup run output dir
    run_dir = Path("results/runs") / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = run_dir / "cache"
    cache_dir.mkdir(exist_ok=True)

    # run critic on each snippet
    predictions = []
    for snippet in snippets:
        result = detect(
            snippet["text"],
            mode=args.mode,
            cache_dir=cache_dir,
            snippet_id=snippet.get("snippet_id", "")
        )

        predictions.append({
            "snippet_id": snippet.get("snippet_id", ""),
            "version": snippet.get("version", ""),
            "text": snippet.get("text", "")[:200],
            "gold_labels": snippet.get("labels", []),
            "predicted_labels": result.get("labels", []),
            "rationales": result.get("rationales", {}),
        })

    # compute metrics
    gold_per_item = [p["gold_labels"] for p in predictions]
    pred_per_item = [p["predicted_labels"] for p in predictions]
    metrics = compute_critic_metrics(gold_per_item, pred_per_item, LABEL_IDS)

    # write predictions CSV
    pred_rows = []
    for p in predictions:
        pred_rows.append({
            "snippet_id": p["snippet_id"],
            "version": p["version"],
            "gold_labels": ";".join(p["gold_labels"]),
            "predicted_labels": ";".join(p["predicted_labels"]),
            "correct": set(p["gold_labels"]) == set(p["predicted_labels"]),
        })

    pred_df = pd.DataFrame(pred_rows)
    pred_path = run_dir / "critic_predictions.csv"
    pred_df.to_csv(pred_path, index=False)
    print(f"[✓] Predictions written to {pred_path}")

    # write summary
    summary = {
        "mode": args.mode,
        "total_snippets": len(snippets),
        "per_label": metrics["per_label"],
        "macro_precision": metrics["macro_precision"],
        "macro_recall": metrics["macro_recall"],
        "macro_f1": metrics["macro_f1"],
        "exact_match_accuracy": metrics["exact_match_accuracy"],
    }

    summary_path = run_dir / "critic_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[✓] Summary written to {summary_path}")

    # print summary
    print(f"\n{'Label':<6} {'Prec':>6} {'Recall':>6} {'F1':>6}")
    print("-" * 30)
    for label in LABEL_IDS:
        lm = metrics["per_label"].get(label, {})
        print(f"{label:<6} {lm.get('precision', 0):.3f}  {lm.get('recall', 0):.3f}  {lm.get('f1', 0):.3f}")
    print("-" * 30)
    print(f"{'Macro':<6} {metrics['macro_precision']:.3f}  {metrics['macro_recall']:.3f}  {metrics['macro_f1']:.3f}")
    print(f"\nExact match accuracy: {metrics['exact_match_accuracy']:.3f}")


if __name__ == "__main__":
    main()
