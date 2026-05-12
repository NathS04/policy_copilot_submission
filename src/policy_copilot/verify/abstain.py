"""Confidence scoring and the abstention gate for the B3 pipeline.

The gate is deliberately deterministic — it only looks at reranker scores —
so abstention decisions are reproducible and easy to audit. We compare the
*max* score across the top-k against a threshold rather than the mean: a
single strongly relevant paragraph is what makes a query answerable, and
the max captures that directly. The threshold is configurable; the default
(0.30) was tuned on the validation split via ``calibrate_threshold``.
"""
from typing import List, Dict
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def compute_confidence(evidence: List[Dict]) -> Dict[str, float]:
    """Return confidence stats (max + top-3 mean) from reranked evidence.

    The top-3 mean is kept for diagnostic logging only; the gate itself uses
    the max. Empty evidence returns zeros, which triggers abstention.
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
    """Return True if the max reranker score is below the threshold.

    Strict ``<`` rather than ``<=``: a score exactly at the threshold is
    treated as marginally answerable and allowed through.
    """
    max_score = confidence.get("max_rerank", 0.0)
    if max_score < threshold:
        logger.info(f"Abstaining: max_rerank={max_score:.4f} < threshold={threshold}")
        return True
    return False


def calibrate_threshold(dev_results: List[Dict]) -> float:
    """Pick the threshold that maximises F1 on the abstention decision.

    Sweeps 0.05 → 0.95 in 0.05 steps. Falls back to 0.30 if the dev set is
    too small to be meaningful.
    """
    if len(dev_results) < 5:
        return 0.30

    # Collect (confidence_score, ground_truth_should_abstain) pairs
    pairs = []
    for r in dev_results:
        conf = r.get("confidence", {}).get("max_rerank", 0.0)
        cat = r.get("category", "")
        should_abstain_gt = cat == "unanswerable"
        pairs.append((conf, should_abstain_gt))

    # Exhaustive sweep — the dev set is small enough that this is cheap
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
