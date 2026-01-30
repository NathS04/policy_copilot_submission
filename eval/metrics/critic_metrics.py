"""
Critic evaluation metrics: per-label precision/recall/F1, macro-averaged, exact match.
"""
from typing import List, Dict


def compute_critic_metrics(gold_labels_per_item: List[List[str]],
                           pred_labels_per_item: List[List[str]],
                           all_labels: List[str]) -> Dict:
    """
    Compute per-label precision/recall/F1 and macro averages.

    Args:
        gold_labels_per_item: list of lists of ground-truth label strings per snippet
        pred_labels_per_item: list of lists of predicted label strings per snippet
        all_labels: list of all possible label IDs (e.g. ["L1","L2",...,"L6"])

    Returns dict with:
        per_label: {label: {tp, fp, fn, precision, recall, f1}}
        macro_precision, macro_recall, macro_f1
        exact_match_accuracy
    """
    # count per-label TP, FP, FN
    counts = {label: {"tp": 0, "fp": 0, "fn": 0} for label in all_labels}

    exact_matches = 0
    total = len(gold_labels_per_item)

    for gold, pred in zip(gold_labels_per_item, pred_labels_per_item):
        gold_set = set(gold)
        pred_set = set(pred)

        if gold_set == pred_set:
            exact_matches += 1

        for label in all_labels:
            in_gold = label in gold_set
            in_pred = label in pred_set

            if in_gold and in_pred:
                counts[label]["tp"] += 1
            elif not in_gold and in_pred:
                counts[label]["fp"] += 1
            elif in_gold and not in_pred:
                counts[label]["fn"] += 1

    # compute per-label metrics
    per_label = {}
    precisions = []
    recalls = []
    f1s = []

    for label in all_labels:
        tp = counts[label]["tp"]
        fp = counts[label]["fp"]
        fn = counts[label]["fn"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        per_label[label] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    # macro averages
    macro_precision = sum(precisions) / len(precisions) if precisions else 0.0
    macro_recall = sum(recalls) / len(recalls) if recalls else 0.0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return {
        "per_label": per_label,
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "exact_match_accuracy": round(exact_matches / total, 4) if total > 0 else 0.0,
    }


def calculate_groundedness_score(records: list[dict]) -> float:
    """
    Average support_rate across answered queries.
    Used in main pipeline metrics, kept for backwards compat.
    """
    rates = []
    for r in records:
        cv = r.get("claim_verification")
        if cv and r.get("answer") != "INSUFFICIENT_EVIDENCE":
            rates.append(cv.get("support_rate", 0.0))
    if not rates:
        return 0.0
    return round(sum(rates) / len(rates), 4)
