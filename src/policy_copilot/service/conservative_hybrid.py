"""B4 Conservative Hybrid Mode (Phase E).

Policy module that, after the post-LLM support-rate gate has fired and the
generative answer has been downgraded to ``INSUFFICIENT_EVIDENCE``,
inspects the retrieved evidence and decides whether to:

  (a) return an extractive paragraph as the response (with citation),
      when retrieval evidence is strong AND the question shape suggests
      the answer can be quoted; or
  (b) abstain (preserve ``INSUFFICIENT_EVIDENCE``) when retrieval is
      weak or the corpus does not appear to answer the question.

Tunable thresholds live in the ``cfg`` dict; the defaults are tuned on
the dev split and never read golden labels at inference time.

This module is **pure**: it takes a response-shaped dict and returns a
new dict. It does no I/O and makes no LLM calls. The orchestrator and
the replay script both call ``apply_b4_fallback_policy`` exactly once
per query, after the support gate has been applied.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------- defaults ----------------------------- #
DEFAULTS = {
    # Top reranker score required to consider retrieval "strong".
    # Reranker scores are sigmoid'd (0..1) for the cross-encoder used in the
    # project; values >= 0.60 are confident on the dev split.
    "b4_rerank_threshold": 0.60,
    # Jaccard token-overlap floor between the question and the top
    # retrieved paragraph. Stops B4 from quoting irrelevant high-rerank
    # paragraphs.
    "b4_overlap_threshold": 0.10,
    # If the question contains a number-question shape (how long, how many,
    # what is the maximum, etc.) prefer extractive when the top retrieved
    # paragraph contains at least one number.
    "b4_prefer_extractive_for_numeric_questions": True,
}

# Question shapes that strongly imply a numeric or definite answer is
# expected. Used by ``_question_is_numeric_shape``.
_NUMERIC_SHAPE_PATTERNS = [
    r"\bhow long\b",
    r"\bhow many\b",
    r"\bhow much\b",
    r"\bwhat is the (?:max|maximum|min|minimum|standard)\b",
    r"\bwhat are the (?:max|maximum|min|minimum|standard)\b",
    r"\bwhen\b",
    r"\bdays?\b.*\?",
    r"\bhours?\b.*\?",
]
_NUMERIC_VALUE_RE = re.compile(r"\b\d+\b")

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
_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return {t for t in _WORD_RE.findall((text or "").lower()) if t not in _STOPWORDS}


def _jaccard_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    union = ta | tb
    return len(inter) / len(union)


def _question_is_numeric_shape(question: str) -> bool:
    q = (question or "").lower()
    for pat in _NUMERIC_SHAPE_PATTERNS:
        if re.search(pat, q):
            return True
    return False


def _top_evidence_strength(top_evidence: List[Dict[str, Any]], question: str) -> Tuple[float, float, Optional[Dict]]:
    """Return (top_rerank_score, top_overlap, top_evidence_dict)."""
    if not top_evidence:
        return 0.0, 0.0, None
    top = top_evidence[0]
    rerank = float(top.get("score_rerank") or top.get("score") or 0.0)
    overlap = _jaccard_overlap(question, top.get("text") or "")
    return rerank, overlap, top


def apply_b4_fallback_policy(
    response: Dict[str, Any],
    top_evidence: List[Dict[str, Any]],
    cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Apply B4 fallback rules to a response that has *already* been
    through the support-rate gate.

    The input ``response`` is expected to carry at least:
      - ``question``  (str)
      - ``answer``    (str)  -- may be "INSUFFICIENT_EVIDENCE" if the gate fired
      - ``citations`` (list[str])
      - ``support_rate`` (float or None) -- from claim_verification

    Returns a new dict that copies ``response`` and adds:
      - ``mode_used``         : "generative" | "extractive_fallback" | "abstained"
      - ``fallback_reason``   : str
      - ``evidence_strength`` : dict {top_rerank, top_overlap, numeric_shape}

    Decision rules (tunable via ``cfg``):
      1. If the support gate did not fire (answer != INSUFFICIENT_EVIDENCE
         and support_rate is not None and >= 0.80), keep the generative
         answer. mode_used = "generative".
      2. Else if top_evidence is empty or top rerank < threshold or top
         overlap < threshold, abstain. mode_used = "abstained".
      3. Else if numeric-question heuristic and top paragraph contains a
         number, fall back to extractive on the top paragraph.
      4. Else fall back to extractive on the top paragraph.

    The extractive fallback returns the top retrieved paragraph as the
    answer text, citing the paragraph by its ``paragraph_id``. This is
    safe by construction: the cited paragraph IS the answer text.
    """
    cfg = {**DEFAULTS, **(cfg or {})}
    out = dict(response)
    answer = (response.get("answer") or "").strip()
    support_rate = response.get("support_rate")
    question = response.get("question") or ""

    top_rerank, top_overlap, top_doc = _top_evidence_strength(top_evidence, question)
    numeric_shape = _question_is_numeric_shape(question)
    out["evidence_strength"] = {
        "top_rerank": round(top_rerank, 4),
        "top_overlap": round(top_overlap, 4),
        "numeric_shape": numeric_shape,
    }

    # Rule 1: keep generative when it passed.
    if answer and answer != "INSUFFICIENT_EVIDENCE" and (
        support_rate is None or float(support_rate) >= 0.80
    ):
        out["mode_used"] = "generative"
        out["fallback_reason"] = None
        return out

    # Rule 2: abstain if retrieval is weak.
    if not top_doc:
        out["mode_used"] = "abstained"
        out["fallback_reason"] = "no_retrieved_evidence"
        return out
    if top_rerank < cfg["b4_rerank_threshold"]:
        out["mode_used"] = "abstained"
        out["fallback_reason"] = f"top_rerank_{top_rerank:.2f}_below_{cfg['b4_rerank_threshold']:.2f}"
        return out
    if top_overlap < cfg["b4_overlap_threshold"]:
        out["mode_used"] = "abstained"
        out["fallback_reason"] = f"top_overlap_{top_overlap:.3f}_below_{cfg['b4_overlap_threshold']:.3f}"
        return out

    # Rules 3-4: extractive fallback on the top paragraph.
    pid = top_doc.get("paragraph_id") or ""
    text = top_doc.get("text") or ""
    if numeric_shape and cfg["b4_prefer_extractive_for_numeric_questions"]:
        has_number = bool(_NUMERIC_VALUE_RE.search(text))
        if has_number:
            out["mode_used"] = "extractive_fallback"
            out["fallback_reason"] = "numeric_shape_top_paragraph_has_number"
            out["answer"] = text
            out["citations"] = [pid]
            out["is_abstained"] = False
            return out

    # Generic extractive fallback.
    out["mode_used"] = "extractive_fallback"
    out["fallback_reason"] = f"top_rerank_{top_rerank:.2f}_overlap_{top_overlap:.3f}_above_thresholds"
    out["answer"] = text
    out["citations"] = [pid]
    out["is_abstained"] = False
    return out
