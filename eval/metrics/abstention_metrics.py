"""
Abstention evaluation metrics.
"""
from typing import List


def calculate_abstention_accuracy(predictions: List[str], ground_truth: List[str]) -> float:
    """
    Calculates the accuracy of abstention decisions.
    predictions: list of answer strings
    ground_truth: list of expected answer strings (INSUFFICIENT_EVIDENCE for unanswerable)
    Returns fraction of correct abstention/non-abstention decisions.
    """
    if not predictions:
        return 0.0

    correct = 0
    for pred, gt in zip(predictions, ground_truth):
        pred_abstained = pred == "INSUFFICIENT_EVIDENCE"
        gt_abstained = gt == "INSUFFICIENT_EVIDENCE"
        if pred_abstained == gt_abstained:
            correct += 1

    return round(correct / len(predictions), 4)


def calculate_abstention_precision(predictions: List[str], ground_truth: List[str]) -> float:
    """Of all queries where system abstained, how many should have been abstained?"""
    abstained = [(p, g) for p, g in zip(predictions, ground_truth)
                 if p == "INSUFFICIENT_EVIDENCE"]
    if not abstained:
        return 0.0
    correct = sum(1 for _, g in abstained if g == "INSUFFICIENT_EVIDENCE")
    return round(correct / len(abstained), 4)


def calculate_abstention_recall(predictions: List[str], ground_truth: List[str]) -> float:
    """Of all queries that should have been abstained, how many were?"""
    should_abstain = [(p, g) for p, g in zip(predictions, ground_truth)
                      if g == "INSUFFICIENT_EVIDENCE"]
    if not should_abstain:
        return 0.0
    correct = sum(1 for p, _ in should_abstain if p == "INSUFFICIENT_EVIDENCE")
    return round(correct / len(should_abstain), 4)
