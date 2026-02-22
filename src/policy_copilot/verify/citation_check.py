"""
Per-claim citation verification.
Tier 1: fast keyword-overlap heuristic (always available).
Tier 2: optional LLM-based verification (if enabled).
"""
import re
from typing import List, Dict, Set
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def _tokenise(text: str) -> Set[str]:
    """Simple whitespace + punctuation tokeniser, lowercased, no stopwords."""
    STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                 "being", "have", "has", "had", "do", "does", "did", "will",
                 "would", "could", "should", "may", "might", "shall", "can",
                 "to", "of", "in", "for", "on", "with", "at", "by", "from",
                 "as", "into", "through", "during", "before", "after", "and",
                 "but", "or", "nor", "not", "so", "yet", "both", "either",
                 "neither", "each", "every", "all", "any", "few", "more",
                 "most", "other", "some", "such", "no", "only", "own",
                 "same", "than", "too", "very", "it", "its", "this", "that",
                 "these", "those", "i", "me", "my", "we", "our", "you", "your",
                 "he", "him", "his", "she", "her", "they", "them", "their"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    return words - STOPWORDS


def _extract_numbers(text: str) -> Set[str]:
    """Extracts numeric strings from text."""
    return set(re.findall(r'\b\d+(?:\.\d+)?\b', text))


def verify_claim_heuristic(claim_text: str, cited_paragraph_texts: List[str],
                           overlap_threshold: float = 0.10) -> Dict:
    """
    Tier 1 verification: checks keyword overlap between claim and cited paragraphs.
    Returns: {supported: bool, jaccard: float, rationale: str}
    """
    if not cited_paragraph_texts:
        return {
            "supported": False,
            "jaccard": 0.0,
            "rationale": "No cited paragraphs provided for this claim"
        }

    claim_tokens = _tokenise(claim_text)
    claim_numbers = _extract_numbers(claim_text)

    if not claim_tokens:
        return {"supported": True, "jaccard": 1.0, "rationale": "Empty claim tokens"}

    # check overlap against ALL cited paragraphs combined
    para_tokens = set()
    para_numbers = set()
    for pt in cited_paragraph_texts:
        para_tokens |= _tokenise(pt)
        para_numbers |= _extract_numbers(pt)

    # Jaccard overlap on content words
    intersection = claim_tokens & para_tokens
    union = claim_tokens | para_tokens
    jaccard = len(intersection) / len(union) if union else 0.0

    # bonus for shared numbers (important for policy facts)
    number_overlap = bool(claim_numbers & para_numbers) if claim_numbers else False

    supported = jaccard >= overlap_threshold or number_overlap

    rationale = f"Jaccard={jaccard:.3f}"
    if number_overlap:
        rationale += ", numeric_match=True"

    return {
        "supported": supported,
        "jaccard": round(jaccard, 4),
        "rationale": rationale,
    }


def verify_claims(claims: List[Dict], evidence_lookup: Dict[str, str],
                  overlap_threshold: float = 0.10,
                  enable_llm: bool = False,
                  cache_dir=None,
                  query_id: str = "") -> Dict:
    """
    Runs verification on all claims.
    Tier 1 (always): keyword overlap heuristic.
    Tier 2 (if enable_llm=True): LLM-based verification with caching.
    evidence_lookup: {paragraph_id: text}
    Returns verification summary dict.
    """
    results = []
    supported_count = 0
    unsupported_count = 0

    for claim in claims:
        # get cited paragraph texts for this claim
        cited_texts = []
        valid_citations = [pid for pid in claim.get("citations", []) if pid in evidence_lookup]
        for pid in valid_citations:
            if pid in evidence_lookup:
                cited_texts.append(evidence_lookup[pid])

        # try Tier 2 first if enabled
        vr = None
        if enable_llm and cited_texts:
            try:
                from policy_copilot.verify.llm_judges import llm_verify_claim
                llm_result = llm_verify_claim(
                    claim["text"], cited_texts,
                    cache_dir=cache_dir,
                    query_id=query_id,
                    claim_id=claim["claim_id"]
                )
                if "supported" in llm_result:
                    vr = {
                        "supported": llm_result["supported"],
                        "jaccard": -1.0,  # not applicable for LLM
                        "rationale": f"LLM: {llm_result.get('rationale', '')}",
                        "quote": llm_result.get("quote", ""),
                        "tier": 2,
                    }
            except Exception as e:
                logger.warning(f"Tier-2 LLM verify failed, falling back: {e}")

        # fallback to Tier 1
        if vr is None:
            vr = verify_claim_heuristic(
                claim["text"], cited_texts, overlap_threshold
            )
            vr["tier"] = 1

        claim_result = {
            "claim_id": claim["claim_id"],
            "text": claim["text"],
            "citations": valid_citations,
            "supported": vr["supported"],
            "support_rationale": vr["rationale"],
            "verification_tier": vr.get("tier", 1),
        }
        if not vr["supported"]:
            claim_result["unsupported_reason"] = vr["rationale"]
            unsupported_count += 1
        else:
            supported_count += 1

        results.append(claim_result)

    total = supported_count + unsupported_count
    support_rate = supported_count / total if total > 0 else 1.0

    return {
        "claims": results,
        "supported_claims": supported_count,
        "unsupported_claims": unsupported_count,
        "support_rate": round(support_rate, 4),
    }


def enforce_support_policy(answer: str, citations: List[str],
                           verification: Dict,
                           min_support_rate: float = 0.80) -> tuple:
    """
    Enforces the min_support_rate policy.
    Returns: (final_answer, final_citations, notes_list)
    """
    notes = []
    support_rate = verification.get("support_rate", 1.0)

    if answer == "INSUFFICIENT_EVIDENCE":
        return answer, [], notes

    if support_rate < min_support_rate:
        # abstain entirely
        notes.append(f"ABSTAINED_LOW_SUPPORT_RATE (rate={support_rate:.2f})")
        return "INSUFFICIENT_EVIDENCE", [], notes

    # check if some claims are unsupported — remove them
    unsupported = [c for c in verification.get("claims", []) if not c["supported"]]
    if unsupported:
        # build answer from only supported claims
        supported_claims = [c for c in verification["claims"] if c["supported"]]
        if supported_claims:
            # rebuild answer from supported claim texts only
            new_answer = " ".join(c["text"] for c in supported_claims)
            # rebuild citations from supported claims only
            new_citations = []
            seen = set()
            for c in supported_claims:
                for pid in c.get("citations", []):
                    if pid not in seen:
                        seen.add(pid)
                        new_citations.append(pid)
            notes.append("UNSUPPORTED_CLAIMS_REMOVED")
            return new_answer, new_citations, notes

    return answer, citations, notes
