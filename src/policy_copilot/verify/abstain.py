"""
Confidence scoring and abstention logic for the B3 pipeline.

Purpose:
    Implements the abstention gate — the mechanism by which Policy Copilot decides
    whether to invoke the LLM or return INSUFFICIENT_EVIDENCE. This is the primary
    deterministic reliability control: it operates entirely on reranker scores,
    making abstention decisions transparent and reproducible.

Design decisions:
    - Abstention uses the *maximum* reranker score rather than the mean of top-k.
      The mean was explored during Sprint 5 (see calibrate_threshold below) but
      rejected because it degraded Abstention Accuracy on unanswerable queries:
      irrelevant paragraphs sometimes receive moderate scores from the cross-encoder,
      inflating the mean above the threshold even when no single paragraph is
      genuinely relevant. The max is more discriminating for the "is there at least
      one relevant passage?" question that abstention fundamentally asks.
    - The threshold (default 0.30) was calibrated on the validation split during
      Sprint 6 using the F1-maximisation procedure in calibrate_threshold(). The
      production threshold may need re-calibration if the retrieval backend changes
      (e.g., switching from BM25 fallback to true dense retrieval), since cross-encoder
      score distributions vary with the quality of the input candidate set.

Parameters (module-level):
    None — all configuration is injected via function arguments from config.py.

# Considered using softmax-normalised scores across all candidates as a
# confidence proxy, but this obscures the absolute quality signal: a set of
# uniformly bad candidates would produce a high softmax for the "least bad"
# option. Raw logit-scale scores preserve the ability to set absolute thresholds.
"""
from typing import List, Dict
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def compute_confidence(evidence: List[Dict]) -> Dict[str, float]:
    """
    Computes confidence metrics from reranked evidence.

    Purpose:
        Extracts summary statistics from the reranker scores attached to each
        evidence candidate. These statistics feed into should_abstain() and are
        also logged for post-hoc analysis in the evaluation pipeline.

    Parameters:
        evidence: List of evidence dicts, each containing 'score_rerank' (float).
                  Expected to be pre-sorted by reranker in descending order.

    Returns:
        Dict with keys:
            - max_rerank (float): Highest reranker score in the candidate set.
            - mean_top3_rerank (float): Mean of the top 3 reranker scores.
              Included for analysis purposes even though abstention uses max only.

    Notes:
        Returns zeros if the evidence list is empty, which triggers abstention
        downstream. This is the correct behaviour: no evidence = no confidence.
    """
    rerank_scores = [e.get("score_rerank", 0.0) for e in evidence]
    if not rerank_scores:
        return {"max_rerank": 0.0, "mean_top3_rerank": 0.0}

    max_score = max(rerank_scores)
    # Top-3 mean retained for diagnostic logging even though abstention uses max
    top3 = sorted(rerank_scores, reverse=True)[:3]
    mean_top3 = sum(top3) / len(top3)

    return {
        "max_rerank": round(max_score, 4),
        "mean_top3_rerank": round(mean_top3, 4),
    }


def should_abstain(confidence: Dict[str, float], threshold: float = 0.30) -> bool:
    """
    Returns True if the system should abstain due to low confidence.

    Purpose:
        Implements the binary abstention gate. If the maximum reranker score
        falls below the threshold, the system refuses to invoke the LLM,
        returning INSUFFICIENT_EVIDENCE instead.

    Parameters:
        confidence: Output of compute_confidence().
        threshold:  Abstention threshold (default 0.30, calibrated on validation split).

    Returns:
        True if the system should abstain; False if it should proceed to generation.

    Design decision:
        The threshold comparison is strict less-than (not <=) because a score
        exactly at the threshold indicates marginal confidence — empirically,
        these borderline cases were more often answerable than not during
        validation-set analysis, so they are allowed through.
    """
    max_score = confidence.get("max_rerank", 0.0)
    if max_score < threshold:
        logger.info(f"Abstaining: max_rerank={max_score:.4f} < threshold={threshold}")
        return True
    return False


def calibrate_threshold(dev_results: List[Dict]) -> float:
    """
    Suggests an abstention threshold by maximising F1 on a development set.

    Purpose:
        Automates threshold selection by sweeping candidate values from 0.05
        to 0.95 and selecting the one that maximises the F1 score of the
        binary abstention decision (abstain on unanswerable, answer on answerable).

    Parameters:
        dev_results: List of per-query result dicts from a development run,
                     each containing 'confidence' (dict) and 'category' (str).

    Returns:
        Recommended threshold (float). Falls back to 0.30 if insufficient data.

    Notes:
        This function was used during Sprint 6 to select the production threshold.
        It is retained in the codebase for reproducibility and for future
        re-calibration if the retrieval backend or corpus changes.
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

    # Sweep thresholds — chosen over grid search with cross-validation
    # because the dev set is small enough that exhaustive sweep is tractable
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
