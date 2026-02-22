"""
Contradiction detection between evidence paragraphs.
Uses deterministic heuristics (always available) with optional LLM judge.
"""
import re
from itertools import combinations
from typing import List, Dict
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

# Antonym / negation pairs to look for
_ANTONYM_PAIRS = [
    ("allowed", "not allowed"), ("allowed", "prohibited"), ("allowed", "forbidden"),
    ("required", "not required"), ("required", "optional"),
    ("must", "must not"), ("shall", "shall not"),
    ("enabled", "disabled"), ("always", "never"),
    ("mandatory", "voluntary"), ("permitted", "banned"),
    ("can", "cannot"), ("should", "should not"),
    ("approve", "reject"), ("include", "exclude"),
]


def _normalise(text: str) -> str:
    return re.sub(r'\s+', ' ', text.lower().strip())


def _check_negation_pair(text_a: str, text_b: str) -> List[str]:
    """Checks if two texts contain antonym/negation conflicts."""
    a_norm = _normalise(text_a)
    b_norm = _normalise(text_b)
    conflicts = []

    for pos, neg in _ANTONYM_PAIRS:
        # check if one text has the positive and the other has the negative
        if (pos in a_norm and neg in b_norm) or (neg in a_norm and pos in b_norm):
            conflicts.append(f"'{pos}' vs '{neg}'")

    return conflicts


def _check_numeric_conflict(text_a: str, text_b: str) -> List[str]:
    """
    Checks if two texts mention the same key phrase with different numbers.
    Example: 'minimum 8 characters' vs 'minimum 12 characters'
    """
    conflicts = []
    # find patterns like "minimum/maximum/at least/at most + number"
    pattern = r'((?:minimum|maximum|at least|at most|no more than|no fewer than)\s+)(\d+)'
    matches_a = re.findall(pattern, text_a.lower())
    matches_b = re.findall(pattern, text_b.lower())

    for prefix_a, num_a in matches_a:
        for prefix_b, num_b in matches_b:
            # same kind of constraint but different number
            if prefix_a.strip() == prefix_b.strip() and num_a != num_b:
                conflicts.append(f"'{prefix_a.strip()} {num_a}' vs '{prefix_b.strip()} {num_b}'")

    return conflicts


def detect_contradictions(evidence: List[Dict],
                          enable_llm: bool = False,
                          cache_dir=None) -> List[Dict]:
    """
    Detects contradictions between pairs of evidence paragraphs.
    Tier 1: heuristic (always). Tier 2: LLM judge (if enable_llm).
    Returns list of contradiction objects.
    """
    contradictions = []

    # only compare pairs — O(n^2) but n is small (typically 5-20)
    for a, b in combinations(evidence, 2):
        text_a = a.get("text", "")
        text_b = b.get("text", "")
        pid_a = a.get("paragraph_id", "?")
        pid_b = b.get("paragraph_id", "?")

        reasons = []

        # check negation/antonym conflicts
        neg_conflicts = _check_negation_pair(text_a, text_b)
        reasons.extend(neg_conflicts)

        # check numeric conflicts
        num_conflicts = _check_numeric_conflict(text_a, text_b)
        reasons.extend(num_conflicts)

        # Tier-2 LLM judge if enabled and heuristic found nothing
        llm_confirmed = False
        if enable_llm and not reasons:
            try:
                from policy_copilot.verify.llm_judges import llm_judge_contradiction
                llm_result = llm_judge_contradiction(a, b, cache_dir=cache_dir)
                if llm_result.get("contradiction"):
                    reasons.append(f"LLM: {llm_result.get('rationale', 'detected')}")
                    llm_confirmed = True
            except Exception as e:
                logger.warning(f"LLM contradiction judge failed: {e}")

        if reasons:
            # assign confidence based on number of conflict signals
            if len(reasons) >= 2:
                confidence = "high"
            elif llm_confirmed:
                confidence = "med"
            elif any("vs" in r and ("must" in r or "required" in r) for r in reasons):
                confidence = "med"
            else:
                confidence = "low"

            contradictions.append({
                "type": "contradiction",
                "paragraph_ids": [pid_a, pid_b],
                "rationale": "; ".join(reasons),
                "confidence": confidence,
                "tier": 2 if llm_confirmed else 1,
            })

    if contradictions:
        logger.info(f"Detected {len(contradictions)} potential contradiction(s)")

    return contradictions


def apply_contradiction_policy(answer: str, citations: List[str],
                               contradictions: List[Dict],
                               policy: str = "surface") -> tuple:
    """
    Adjusts the answer based on detected contradictions.
    policy: 'surface' (default) or 'abstain_on_high'
    Returns: (adjusted_answer, adjusted_citations, notes_list)
    """
    notes = []
    if not contradictions:
        return answer, citations, notes

    if answer == "INSUFFICIENT_EVIDENCE":
        return answer, citations, notes

    high_conf = [c for c in contradictions if c["confidence"] == "high"]

    if policy == "abstain_on_high" and high_conf:
        notes.append("ABSTAINED_CONTRADICTION_HIGH")
        return "INSUFFICIENT_EVIDENCE", [], notes

    # surface policy: add conflict note and cite both sides
    conflict_pids = set()
    for c in contradictions:
        conflict_pids.update(c["paragraph_ids"])

    # add any missing conflict paragraph_ids to citations
    for pid in conflict_pids:
        if pid not in citations:
            citations.append(pid)

    conflict_summary = "; ".join(c["rationale"] for c in contradictions[:3])
    answer += f" Note: some evidence sources may conflict on this point ({conflict_summary})."
    notes.append("CONTRADICTION_SURFACED")

    return answer, citations, notes
