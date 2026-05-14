"""Quantitative policy-fact extraction (Phase H).

Extracts ``(subject, comparator, value, unit, paragraph_id)`` tuples
from policy paragraph text so that two paragraphs about the same
subject and unit can be flagged as a quantitative conflict when their
values differ.

Examples that this module is designed to catch in the project corpus:

  - "passwords must be a minimum of 8 characters" (handbook)
    vs "passwords must now be a minimum of 12 characters" (addendum)
    → conflict on subject {password, characters}, values 8 vs 12.

  - "remote work up to 3 days per week" (handbook)
    vs "minimum of 5 days per week in-office" (addendum)
    → reported via subject {remote work, in-office}; not a direct
    numeric conflict on the same subject — handled by the existing
    antonym detector ('up to' vs 'minimum').

  - "password rotation period of 90 days" (handbook)
    vs "password rotation period is reduced to 60 days" (addendum)
    → conflict on subject {password rotation, days}, values 60 vs 90.

No LLM calls. Pure regex + token-overlap heuristic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional


# ---------- unit normalisation ----------

# Map raw unit token (lowercased, singular) -> canonical unit family.
_UNIT_MAP = {
    "day": "days",
    "days": "days",
    "hour": "hours",
    "hours": "hours",
    "minute": "minutes",
    "minutes": "minutes",
    "min": "minutes",
    "week": "weeks",
    "weeks": "weeks",
    "month": "months",
    "months": "months",
    "year": "years",
    "years": "years",
    "character": "chars",
    "characters": "chars",
    "char": "chars",
    "chars": "chars",
    "letter": "chars",
    "letters": "chars",
    "word": "words",
    "words": "words",
    "attempt": "attempts",
    "attempts": "attempts",
}


def _canon_unit(raw: str) -> Optional[str]:
    return _UNIT_MAP.get((raw or "").lower())


# ---------- subject extraction ----------

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "at", "for", "with", "by", "from", "as",
    "and", "or", "but", "not", "this", "that", "these", "those",
    "it", "its", "they", "them", "their", "we", "our", "you", "your",
    "i", "my", "me", "do", "does", "did", "have", "has", "had",
    "can", "could", "would", "should", "may", "might", "will", "shall",
    "must", "now", "least", "most", "more", "less", "no", "fewer", "any", "every",
    "up", "down",
}

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-]*")
_NUM_RE = re.compile(r"\b(\d+)\s+([A-Za-z]+)")
# Comparator words that often precede a number.
_COMPARATORS = {
    "minimum", "maximum", "least", "most", "more", "less",
    "every", "within", "up", "over", "under", "no",
}


@dataclass
class PolicyFact:
    subject: str           # short noun phrase
    subject_tokens: tuple  # frozen tokens for cheap comparison
    comparator: Optional[str]
    value: int
    unit: str              # canonical
    paragraph_id: str
    raw_phrase: str

    def to_dict(self):
        return {
            "subject": self.subject,
            "comparator": self.comparator,
            "value": self.value,
            "unit": self.unit,
            "paragraph_id": self.paragraph_id,
            "raw_phrase": self.raw_phrase,
        }


def _tokenise(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text)]


def _subject_phrase(tokens_before: List[str], k: int = 6) -> str:
    """Pick the last k non-stopword tokens before the number as the subject."""
    keep = [t for t in tokens_before if t not in _STOPWORDS]
    return " ".join(keep[-k:])


def extract_policy_facts(text: str, paragraph_id: str = "") -> List[PolicyFact]:
    """Extract `(value, unit)` tuples with their nearby subject phrase.

    Returns a list of `PolicyFact`. One paragraph can produce multiple
    facts. The same paragraph may have several numeric statements (e.g.
    "8 characters" + "90 days" + "30 minutes") — each becomes its own
    fact.
    """
    facts: List[PolicyFact] = []
    if not text:
        return facts

    for m in _NUM_RE.finditer(text):
        raw_num, raw_unit = m.group(1), m.group(2)
        canon_unit = _canon_unit(raw_unit)
        if not canon_unit:
            continue
        try:
            value = int(raw_num)
        except ValueError:
            continue

        # Look at the preceding window for a subject + optional comparator.
        before = text[: m.start()]
        before_tokens = _tokenise(before)
        # Strip the very last few stopwords; they're usually "of", "a", etc.
        comparator = None
        if before_tokens:
            for cand in reversed(before_tokens[-5:]):
                if cand in _COMPARATORS:
                    comparator = cand
                    break

        subject = _subject_phrase(before_tokens, k=6)
        subject_tokens = tuple(sorted(set(_tokenise(subject))))

        raw_phrase = (
            (" ".join(before_tokens[-4:]) + f" {value} {raw_unit}").strip()
        )
        facts.append(
            PolicyFact(
                subject=subject,
                subject_tokens=subject_tokens,
                comparator=comparator,
                value=value,
                unit=canon_unit,
                paragraph_id=paragraph_id,
                raw_phrase=raw_phrase,
            )
        )
    return facts


# ---------- conflict detection ----------

_SUBJECT_OVERLAP_FLOOR = 2  # minimum shared tokens between subjects


def _subject_overlap(a: PolicyFact, b: PolicyFact) -> int:
    return len(set(a.subject_tokens) & set(b.subject_tokens))


def find_quantitative_conflicts(
    facts_a: Iterable[PolicyFact],
    facts_b: Iterable[PolicyFact],
) -> List[dict]:
    """Return a list of conflict objects between two paragraphs' facts."""
    a_list = list(facts_a)
    b_list = list(facts_b)
    conflicts: List[dict] = []
    for fa in a_list:
        for fb in b_list:
            if fa.unit != fb.unit:
                continue
            if fa.value == fb.value:
                continue
            if _subject_overlap(fa, fb) < _SUBJECT_OVERLAP_FLOOR:
                continue
            conflicts.append({
                "type": "numeric_conflict",
                "subject": fa.subject if len(fa.subject) >= len(fb.subject) else fb.subject,
                "unit": fa.unit,
                "values": [fa.value, fb.value],
                "paragraph_ids": [fa.paragraph_id, fb.paragraph_id],
                "rationale": (
                    f"{fa.subject!r} {fa.value} {fa.unit} vs "
                    f"{fb.subject!r} {fb.value} {fb.unit}"
                ),
                "tier": 1,
            })
    return conflicts
