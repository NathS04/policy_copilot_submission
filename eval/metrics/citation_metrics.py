"""
Citation evaluation metrics.
"""
from typing import List


def calculate_citation_precision(generated_citations: List[str],
                                  retrieved_ids: List[str]) -> float:
    """
    Fraction of generated citations that are valid (exist in retrieved set).
    Returns 0.0 if no citations are made (cannot credit precision for silence).
    """
    if not generated_citations:
        return 0.0
    retrieved_set = set(retrieved_ids)
    valid = sum(1 for c in generated_citations if c in retrieved_set)
    return round(valid / len(generated_citations), 4)


def calculate_citation_recall(generated_citations: List[str],
                               gold_ids: List[str]) -> float:
    """
    Fraction of gold paragraph_ids that appear in the generated citations.
    """
    if not gold_ids:
        return 1.0  # no gold ids = nothing to recall (correctly abstained from citing)
    gen_set = set(generated_citations)
    found = sum(1 for g in gold_ids if g in gen_set)
    return round(found / len(gold_ids), 4)


def calculate_ungrounded_rate(records: list[dict]) -> float | None:
    """
    Fraction of claims that are unsupported across all records.
    Returns None if no verification data exists (e.g. B1/B2 without verifier).
    """
    total_claims = 0
    unsupported = 0
    verification_present = False

    for r in records:
        cv = r.get("claim_verification")
        if cv:
            verification_present = True
            if r.get("answer") != "INSUFFICIENT_EVIDENCE":
                total_claims += cv.get("supported_claims", 0) + cv.get("unsupported_claims", 0)
                unsupported += cv.get("unsupported_claims", 0)
    
    if not verification_present:
        return None
        
    if total_claims == 0:
        return 0.0
    return round(unsupported / total_claims, 4)
