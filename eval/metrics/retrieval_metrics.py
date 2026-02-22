"""
Retrieval evaluation metrics.
"""
from typing import List


def calculate_recall_at_k(retrieved_ids: List[str], gold_ids: List[str],
                          k: int = 5) -> float:
    """
    Recall@k: fraction of gold paragraph_ids found in top-k retrieved.
    """
    if not gold_ids:
        return 1.0  # no gold ids = nothing to miss
    top_k = set(retrieved_ids[:k])
    found = sum(1 for g in gold_ids if g in top_k)
    return round(found / len(gold_ids), 4)


def calculate_mrr(retrieved_ids: List[str], gold_ids: List[str]) -> float:
    """
    Mean Reciprocal Rank: 1/(rank of first relevant result).
    """
    if not gold_ids:
        return 1.0
    gold_set = set(gold_ids)
    for i, rid in enumerate(retrieved_ids):
        if rid in gold_set:
            return round(1.0 / (i + 1), 4)
    return 0.0


def calculate_precision_at_k(retrieved_ids: List[str], gold_ids: List[str],
                              k: int = 5) -> float:
    """
    Precision@k: fraction of top-k retrieved that are in gold set.
    """
    if not retrieved_ids or k == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    gold_set = set(gold_ids)
    relevant = sum(1 for r in top_k if r in gold_set)
    return round(relevant / len(top_k), 4)
