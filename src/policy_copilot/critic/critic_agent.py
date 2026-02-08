"""
Critic agent: detects problematic policy language patterns (L1–L6).
Tier 1: lexicon-based heuristics (always available).
Tier 2: LLM-based classification (optional, cached).
"""
import hashlib
import json
import re
from pathlib import Path
from typing import Optional

from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


# ------------------------------------------------------------------ #
#  Tier 1: Heuristic detection                                         #
# ------------------------------------------------------------------ #

# L1: normative/loaded language triggers
_L1_TRIGGERS = [
    "obviously", "clearly", "of course", "reasonable people", "everyone knows",
    "undeniably", "unquestionably", "without doubt", "needless to say",
    "it goes without saying", "self-evident", "beyond question",
    "any sensible", "right-thinking", "no sane person",
]

# L2: framing imbalance triggers
_L2_TRIGGERS = [
    "merely", "just a", "only a", "simply a", "nothing more than",
    "the sole", "the only", "exclusively", "entirely due to",
]

# L3: unsupported claim triggers
_L3_TRIGGERS = [
    "proves", "guarantees", "ensures", "eliminates all",
    "without exception", "in every case", "universally",
    "has been proven", "is certain to", "will definitely",
    "beyond any doubt", "impossible to fail",
]

# L4: internal contradiction patterns (must vs must not in same snippet)
_L4_PAIRS = [
    ("must", "must not"), ("required", "not required"), ("required", "optional"),
    ("shall", "shall not"), ("mandatory", "voluntary"),
    ("allowed", "not allowed"), ("allowed", "prohibited"),
]

# L5: false dilemma triggers
_L5_TRIGGERS = [
    "either .{1,30} or", "only two options", "only two choices",
    "no alternative", "the only choice", "we must choose between",
    "no other option", "binary choice", "two paths",
]

# L6: slippery slope triggers
_L6_TRIGGERS = [
    "will inevitably", "inevitably lead", "eventually results in",
    "leads to", "opens the door to", "sets a dangerous precedent",
    "slippery slope", "domino effect", "cascade of",
    "will certainly cause", "unstoppable",
]


def _check_triggers(text: str, triggers: list[str], is_regex: bool = False) -> list[str]:
    """Returns list of matched trigger phrases."""
    text_lower = text.lower()
    matches = []
    for trigger in triggers:
        if is_regex:
            if re.search(trigger, text_lower):
                matches.append(trigger)
        else:
            if trigger in text_lower:
                matches.append(trigger)
    return matches


def detect_heuristic(text: str) -> dict:
    """
    Run Tier-1 heuristic detection on a text snippet.
    Returns: {labels: [str], rationales: {label: [triggers]}}
    """
    labels = []
    rationales = {}

    # L1: normative/loaded language
    l1 = _check_triggers(text, _L1_TRIGGERS)
    if l1:
        labels.append("L1")
        rationales["L1"] = l1

    # L2: framing imbalance
    l2 = _check_triggers(text, _L2_TRIGGERS)
    if l2:
        labels.append("L2")
        rationales["L2"] = l2

    # L3: unsupported claim
    l3 = _check_triggers(text, _L3_TRIGGERS)
    if l3:
        labels.append("L3")
        rationales["L3"] = l3

    # L4: internal contradiction (both sides in same snippet)
    for pos, neg in _L4_PAIRS:
        text_lower = text.lower()
        if pos in text_lower and neg in text_lower:
            if "L4" not in labels:
                labels.append("L4")
                rationales["L4"] = []
            rationales["L4"].append(f"'{pos}' and '{neg}' both present")

    # L5: false dilemma
    l5 = _check_triggers(text, _L5_TRIGGERS, is_regex=True)
    if l5:
        labels.append("L5")
        rationales["L5"] = l5

    # L6: slippery slope
    l6 = _check_triggers(text, _L6_TRIGGERS)
    if l6:
        labels.append("L6")
        rationales["L6"] = l6

    return {"labels": labels, "rationales": rationales}


# ------------------------------------------------------------------ #
#  Tier 2: LLM-based classification                                    #
# ------------------------------------------------------------------ #

_CRITIC_SYSTEM = """You are a policy language critic.
Analyse the given text snippet for these issues:
L1 = Normative/loaded language (emotional, biased wording)
L2 = Framing imbalance (one-sided perspective)
L3 = Unsupported claim (strong assertion without evidence)
L4 = Internal contradiction (conflicting statements)
L5 = False dilemma (only two options presented)
L6 = Slippery slope (unjustified causal chain to extreme)

Rules:
1. Return ONLY valid JSON.
2. Only flag labels where there is CLEAR evidence in the text.
3. Provide a brief rationale for each flagged label.

Output format:
{"labels": ["L1", "L3"], "rationales": {"L1": "uses 'obviously' loaded term", "L3": "claims 'guarantees success' without evidence"}}

If no issues found: {"labels": [], "rationales": {}}
"""

_CRITIC_USER = """Analyse this policy text snippet:

---
{text}
---

Return JSON only:"""


def detect_llm(text: str, cache_dir: Optional[Path] = None,
               snippet_id: str = "") -> dict:
    """
    Run Tier-2 LLM-based critic on a text snippet.
    Returns: {labels: [str], rationales: {label: str}}
    Falls back to heuristic on error.
    """
    key = hashlib.sha256(text.encode()).hexdigest()[:16]

    # check cache
    if cache_dir:
        cache_path = cache_dir / "critic_llm.jsonl"
        if cache_path.exists():
            with open(cache_path, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj.get("_cache_key") == key:
                            return obj
                    except json.JSONDecodeError:
                        pass

    try:
        from policy_copilot.verify.llm_judges import _call_llm, _parse_json_response
        raw = _call_llm(_CRITIC_SYSTEM, _CRITIC_USER.format(text=text))
        result = _parse_json_response(raw)
        if "labels" not in result:
            logger.warning("LLM critic missing 'labels' key, falling back")
            return detect_heuristic(text)
    except Exception as e:
        logger.error(f"LLM critic failed: {e}")
        return detect_heuristic(text)

    # cache
    result["_cache_key"] = key
    result["snippet_id"] = snippet_id
    if cache_dir:
        cache_path = cache_dir / "critic_llm.jsonl"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "a") as f:
            f.write(json.dumps(result) + "\n")

    return result


def detect(text: str, mode: str = "heuristic",
           cache_dir: Optional[Path] = None,
           snippet_id: str = "") -> dict:
    """
    Main entry point for critic detection.
    mode: 'heuristic' or 'llm'
    Returns: {labels: [str], rationales: {label: ...}}
    """
    if mode == "llm":
        return detect_llm(text, cache_dir=cache_dir, snippet_id=snippet_id)
    return detect_heuristic(text)
