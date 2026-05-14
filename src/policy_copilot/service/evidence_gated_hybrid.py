"""B5 Evidence-Gated Hybrid — deterministic answerability gate.

B5 reuses the same top-5 reranked evidence as B3-Extractive Hybrid and
applies a deterministic answerability gate. No LLM calls. Citations are
always real paragraph IDs from the retrieved evidence; B5 never returns
uncited text.

The gate's purpose is to push B3-Extractive's Abstention Accuracy
(currently 76.9% on the corrected v2 set, with 3 unanswerable false
positives) up to >= 80% without losing too many answerable queries.

Decision rules (in order):
  1. retrieval too weak                  -> abstain
  2. lexical overlap below floor          -> abstain
  3. top paragraph matches GENERIC_PATTERNS -> abstain
  4. high rerank + low overlap + question
     qualifier missing from top paragraph -> abstain  (the "anomaly")
  5. numeric question + no digit in top
     paragraph                            -> abstain
  6. else                                  -> surface extractive answer

QUALIFIER_TERMS is a fixed dictionary of policy-domain discriminating
words. It is NOT derived from gold labels or query IDs.

Optional contradiction-aware mode: if the existing contradiction
detector reports >= 1 conflict in the retrieved evidence AND at least
two distinct conflict paragraph IDs are within the top-5, B5 surfaces
an answer that concatenates both paragraphs (both citations).
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ----------------------------- defaults ----------------------------- #
DEFAULTS: Dict[str, Any] = {
    # Permissive floor on top reranker score. The hybrid pipeline saturates
    # at high values for almost every query, so this only catches genuine
    # non-matches (rerank near 0).
    "rerank_floor": 0.05,
    # Lexical Jaccard overlap floor (stopwords stripped). Tuned on dev split.
    "overlap_floor": 0.058,
    # "High rerank, low overlap, question qualifier missing" anomaly gate.
    "high_rerank": 0.95,
    "low_overlap_cutoff": 0.058,
    # If True, abstain on numeric questions whose top paragraph has no digit.
    "numeric_filter": True,
    # If True, apply the qualifier-missing anomaly filter.
    "qualifier_filter": True,
    # If True, abstain on top paragraphs matching GENERIC_PATTERNS.
    "generic_filter": True,
}


# Static dictionary of qualifier tokens — policy-domain discriminators.
# This list is intentionally generic. It is NOT derived from the golden
# set or any gold paragraph IDs.
QUALIFIER_TERMS: set = {
    # Employment status
    "part-time", "part", "full-time", "intern", "contractor",
    "senior", "junior", "executive", "manager",
    # Location / scope
    "overseas", "abroad", "international", "remote", "office", "home",
    # Data classification polarity
    "non-sensitive", "public", "confidential", "restricted",
    "sensitive",
    # Device ownership
    "byod",
    # Frequency
    "annual", "quarterly", "monthly", "weekly", "daily",
    # Action polarity
    "permitted", "prohibited", "optional", "mandatory",
}


# Patterns that mark a paragraph as too generic to support a confident
# extractive answer.
GENERIC_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bemployees must follow (the )?policy\b", re.IGNORECASE),
    re.compile(r"\bprocedures may vary\b", re.IGNORECASE),
    re.compile(r"\bwhere appropriate\b", re.IGNORECASE),
    re.compile(r"\bas needed\b", re.IGNORECASE),
]


_NUMERIC_SHAPE_PATTERNS = [
    r"\bhow long\b",
    r"\bhow many\b",
    r"\bhow much\b",
    r"\bhow often\b",
    r"\bwhat is the (max|maximum|min|minimum|standard)\b",
    r"\bwhat are the (max|maximum|min|minimum|standard)\b",
    r"\bminimum\b",
    r"\bmaximum\b",
    r"\bwithin\b.*\?",
    r"\bperiod\b",
    r"\bdays?\b.*\?",
    r"\bhours?\b.*\?",
    r"\bmonths?\b.*\?",
]
_DIGIT_RE = re.compile(r"\d")

# A question that asks about a contradiction looks like:
#   "Are passwords both required and optional..."
#   "Is X allowed but Y prohibited..."
#   "Does the policy both require and prohibit Z..."
# The lexical signature is one of:
#   - "both X and Y" / "X and not X" / "X but Y" / "X versus/vs Y" /
#     "conflicting" / "contradict" / "different sections"
_CONTRADICTION_SHAPE_PATTERNS = [
    r"\bboth\b.*\band\b",
    r"\bbut\b.*\b(not|prohibited|forbidden|optional|disallowed)\b",
    r"\b(conflict|contradict|inconsist)",
    r"\bdifferent (sections?|parts?)\b",
    r"\bversus\b",
    r"\bvs\.?\b",
]


def _question_is_contradiction_shape(question: str) -> bool:
    q = (question or "").lower()
    for pat in _CONTRADICTION_SHAPE_PATTERNS:
        if re.search(pat, q):
            return True
    return False


_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "at", "for", "with", "by", "from", "as",
    "and", "or", "but", "not", "this", "that", "these", "those",
    "it", "its", "they", "them", "their", "we", "our", "you", "your",
    "i", "my", "me", "do", "does", "did", "have", "has", "had",
    "can", "could", "would", "should", "may", "might", "will", "shall",
    "what", "when", "where", "who", "whom", "why", "how", "which",
    "if", "then", "than", "so", "any", "all", "some", "no",
    "company", "employee", "employees", "policy", "policies",
}
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-]*")


def _tokens(text: str) -> set:
    if not text:
        return set()
    return {t for t in _WORD_RE.findall(text.lower()) if t not in _STOPWORDS}


def _jaccard_overlap(question: str, paragraph: str) -> float:
    tq, tp = _tokens(question), _tokens(paragraph)
    if not tq or not tp:
        return 0.0
    return len(tq & tp) / len(tq | tp)


def _question_is_numeric_shape(question: str) -> bool:
    q = (question or "").lower()
    for pat in _NUMERIC_SHAPE_PATTERNS:
        if re.search(pat, q):
            return True
    return False


def _extract_qualifiers(question: str) -> List[str]:
    q_lower = (question or "").lower()
    found = []
    for term in QUALIFIER_TERMS:
        # whole-word / hyphen-aware match
        if re.search(r"\b" + re.escape(term) + r"\b", q_lower):
            found.append(term)
    return found


def _is_generic_paragraph(text: str) -> bool:
    if not text:
        return True
    for pat in GENERIC_PATTERNS:
        if pat.search(text):
            return True
    # Very short paragraphs are also generic.
    if len(text.strip()) < 30:
        return True
    return False


def _qualifiers_present_in(qualifiers: Iterable[str], paragraph_text: str) -> bool:
    """Return True iff every qualifier in `qualifiers` appears in the paragraph.

    The anomaly rule fires when this returns False — i.e., at least one of
    the question's qualifying tokens is missing from the top paragraph.
    """
    if not paragraph_text:
        return False
    qlist = list(qualifiers)
    if not qlist:
        return True  # vacuous truth: no qualifiers to check
    pl = paragraph_text.lower()
    return all(
        re.search(r"\b" + re.escape(q) + r"\b", pl) for q in qlist
    )


def _evaluate_features(
    question: str, top_evidence: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Return (gate_features_dict, top_paragraph_or_None)."""
    if not top_evidence:
        return (
            {
                "top_rerank": 0.0,
                "top_overlap": 0.0,
                "qualifier_in_top": False,
                "generic_paragraph": False,
                "top_has_digit": False,
                "is_numeric_q": _question_is_numeric_shape(question),
                "qualifiers": [],
            },
            None,
        )
    top = top_evidence[0]
    top_text = top.get("text") or ""
    qualifiers = _extract_qualifiers(question)
    features = {
        "top_rerank": float(top.get("score_rerank") or top.get("score") or 0.0),
        "top_overlap": round(_jaccard_overlap(question, top_text), 4),
        "qualifier_in_top": _qualifiers_present_in(qualifiers, top_text),
        "generic_paragraph": _is_generic_paragraph(top_text),
        "top_has_digit": bool(_DIGIT_RE.search(top_text)),
        "is_numeric_q": _question_is_numeric_shape(question),
        "qualifiers": qualifiers,
    }
    return features, top


def _contradiction_aware_surface(
    question: str,
    contradictions: Optional[List[Dict[str, Any]]],
    top_evidence: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """If the question itself looks like a contradiction probe AND a
    detected contradiction includes >=2 distinct paragraph IDs inside
    the top-5, return a combined-evidence response. Else None.

    The question-shape gate prevents the contradiction-aware path from
    firing on every query that happens to retrieve evidence with an
    incidental antonym pair somewhere in the top-5.
    """
    if not contradictions:
        return None
    if not _question_is_contradiction_shape(question):
        return None
    evidence_ids = {e.get("paragraph_id") for e in (top_evidence or [])[:5]}
    for c in contradictions:
        pids = c.get("paragraph_ids") or []
        distinct = [p for p in pids if p in evidence_ids]
        if len(distinct) >= 2:
            # Find the matching paragraphs in top_evidence for their text.
            cited_texts = []
            cited_ids = []
            for pid in distinct[:2]:
                for e in top_evidence:
                    if e.get("paragraph_id") == pid:
                        cited_texts.append(e.get("text") or "")
                        cited_ids.append(pid)
                        break
            if len(cited_texts) >= 2:
                combined = (
                    cited_texts[0]
                    + "\n\n[NOTE: A contradicting statement was retrieved.]\n\n"
                    + cited_texts[1]
                )
                return {
                    "mode_used": "surfaced_contradiction_aware",
                    "is_abstained": False,
                    "answer": combined,
                    "citations": cited_ids,
                    "answerability_decision": "surfaced",
                    "answerability_reason": "contradiction_both_sides_retrieved",
                    "selected_citation_ids": cited_ids,
                }
    return None


def apply_b5_gate(
    question: str,
    top_evidence: List[Dict[str, Any]],
    contradictions: Optional[List[Dict[str, Any]]] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Apply the B5 answerability gate over a top-5 evidence list.

    Returns a response dict with mode_used, answer, citations,
    is_abstained, answerability_decision, answerability_reason,
    evidence_strength, gate_features, selected_citation_ids.

    No I/O. No LLM. No golden-set access. The caller is responsible for
    pairing this response with downstream scoring against the corrected
    golden set.
    """
    cfg = {**DEFAULTS, **(cfg or {})}
    features, top = _evaluate_features(question, top_evidence or [])

    # Contradiction-aware path takes precedence if both sides retrieved
    # AND the question itself asks about a contradiction.
    ca = _contradiction_aware_surface(question, contradictions, top_evidence or [])
    if ca is not None:
        ca["evidence_strength"] = {
            "top_rerank": features["top_rerank"],
            "top_overlap": features["top_overlap"],
            "qualifier_in_top": features["qualifier_in_top"],
            "generic_paragraph": features["generic_paragraph"],
            "top_has_digit": features["top_has_digit"],
            "is_numeric_q": features["is_numeric_q"],
        }
        ca["gate_features"] = features
        return ca

    # Rule 1: retrieval too weak.
    if not top or features["top_rerank"] < cfg["rerank_floor"]:
        return _abstain(features, "retrieval_weak_top_rerank_below_floor")

    # Rule 2: lexical overlap floor.
    if features["top_overlap"] < cfg["overlap_floor"]:
        return _abstain(
            features,
            f"overlap_{features['top_overlap']:.3f}_below_floor_{cfg['overlap_floor']:.3f}",
        )

    # Rule 3: generic paragraph.
    if cfg["generic_filter"] and features["generic_paragraph"]:
        return _abstain(features, "top_paragraph_generic")

    # Rule 4: high-rerank + low-overlap + qualifier-missing anomaly.
    if (
        cfg["qualifier_filter"]
        and features["top_rerank"] >= cfg["high_rerank"]
        and features["top_overlap"] < cfg["low_overlap_cutoff"]
        and features["qualifiers"]
        and not features["qualifier_in_top"]
    ):
        return _abstain(
            features,
            f"qualifier_missing_high_rerank_anomaly[{','.join(features['qualifiers'][:3])}]",
        )

    # Rule 5: numeric question requires a digit in the top paragraph.
    if cfg["numeric_filter"] and features["is_numeric_q"] and not features["top_has_digit"]:
        return _abstain(features, "numeric_q_no_digit_in_top_paragraph")

    # Surface the extractive answer.
    pid = top.get("paragraph_id")
    text = top.get("text") or ""
    return {
        "mode_used": "surfaced",
        "is_abstained": False,
        "answer": text,
        "citations": [pid] if pid else [],
        "answerability_decision": "surfaced",
        "answerability_reason": "passed_all_gates",
        "selected_citation_ids": [pid] if pid else [],
        "evidence_strength": {
            "top_rerank": features["top_rerank"],
            "top_overlap": features["top_overlap"],
            "qualifier_in_top": features["qualifier_in_top"],
            "generic_paragraph": features["generic_paragraph"],
            "top_has_digit": features["top_has_digit"],
            "is_numeric_q": features["is_numeric_q"],
        },
        "gate_features": features,
    }


def _abstain(features: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {
        "mode_used": "abstained",
        "is_abstained": True,
        "answer": "INSUFFICIENT_EVIDENCE",
        "citations": [],
        "answerability_decision": "abstained",
        "answerability_reason": reason,
        "selected_citation_ids": [],
        "evidence_strength": {
            "top_rerank": features["top_rerank"],
            "top_overlap": features["top_overlap"],
            "qualifier_in_top": features["qualifier_in_top"],
            "generic_paragraph": features["generic_paragraph"],
            "top_has_digit": features["top_has_digit"],
            "is_numeric_q": features["is_numeric_q"],
        },
        "gate_features": features,
    }
