"""
Confidence scoring and abstention logic for B3.
Decides whether the system should answer or return INSUFFICIENT_EVIDENCE.
"""
from typing import List, Dict
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def compute_confidence(evidence: List[Dict]) -> Dict[str, float]:
    """
    Computes confidence metrics from reranked evidence.
    Returns dict with max_rerank and mean_top3_rerank scores.
    """
    rerank_scores = [e.get("score_rerank", 0.0) for e in evidence]
    if not rerank_scores:
        return {"max_rerank": 0.0, "mean_top3_rerank": 0.0}

    max_score = max(rerank_scores)
    top3 = sorted(rerank_scores, reverse=True)[:3]
    mean_top3 = sum(top3) / len(top3)

    return {
        "max_rerank": round(max_score, 4),
        "mean_top3_rerank": round(mean_top3, 4),
    }


def should_abstain(confidence: Dict[str, float], threshold: float = 0.30) -> bool:
    """
    Returns True if the system should abstain due to low confidence.
    Uses max_rerank score against the threshold.
    """
    max_score = confidence.get("max_rerank", 0.0)
    if max_score < threshold:
        logger.info(f"Abstaining: max_rerank={max_score:.4f} < threshold={threshold}")
        return True
    return False


def calibrate_threshold(dev_results: List[Dict]) -> float:
    """
    Optional: suggests a threshold from dev-set results.
    Finds threshold that maximises F1 of abstention on unanswerable queries.
    Returns suggested threshold (or default 0.30 if not enough data).
    """
    if len(dev_results) < 5:
        return 0.30

    # collect (confidence, should_have_abstained) pairs
    pairs = []
    for r in dev_results:
        conf = r.get("confidence", {}).get("max_rerank", 0.0)
        cat = r.get("category", "")
        should_abstain_gt = cat == "unanswerable"
        pairs.append((conf, should_abstain_gt))

    # try thresholds from 0.05 to 0.95
    best_f1, best_t = 0.0, 0.30
    for t_int in range(5, 96, 5):
        t = t_int / 100.0
        tp = sum(1 for c, s in pairs if c < t and s)
        fp = sum(1 for c, s in pairs if c < t and not s)
        fn = sum(1 for c, s in pairs if c >= t and s)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        if f1 > best_f1:
            best_f1 = f1
            best_t = t

    logger.info(f"Calibrated threshold: {best_t} (F1={best_f1:.3f})")
    return best_t
