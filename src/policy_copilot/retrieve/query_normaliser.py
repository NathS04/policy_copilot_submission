"""Project-local policy-domain query normaliser (Phase 4).

Expands common policy-domain synonyms before retrieval. The original
query is preserved by the caller for citation/audit; the normaliser
returns a *retrieval-only* expanded form.

The dictionary is derived from common policy vocabulary (handbook
section headings, IT-Sec addendum titles, HR-procedure terminology) and
does NOT inspect the golden set. Each mapping is a one-way "add these
extra tokens if the source token appears" — no question replacement, so
queries never lose information.
"""
from __future__ import annotations

import re
from typing import Tuple


# (source_pattern → space-separated extra tokens to append).
# Patterns are case-insensitive whole-word matches. Extras are added
# only once per source pattern even if it appears multiple times.
_EXPANSIONS = [
    # HR / employment
    (r"\bresignation\b",          "leaving company notice period"),
    (r"\bnotice period\b",        "resignation leaving"),
    (r"\bgrievance\b",            "complaint procedure raise concern"),
    (r"\bcomplaint\b",            "grievance"),
    (r"\bdisciplinary\b",         "warning sanction procedure"),
    (r"\bsabbatical\b",           "unpaid leave career break extended"),
    (r"\bprobation\b",            "probationary review onboarding"),
    (r"\bmoonlighting\b",         "secondary employment outside work"),
    (r"\bsecondary employment\b", "moonlighting outside work"),
    (r"\bexit\b",                 "leaving offboarding"),
    # IT / security
    (r"\bbyod\b",                 "bring your own device personal devices"),
    (r"\bpersonal devices?\b",    "BYOD bring own device"),
    (r"\bmulti-factor\b",         "MFA two factor authentication"),
    (r"\bmfa\b",                  "multi-factor two factor authentication"),
    (r"\btwo[- ]?factor\b",       "MFA multi-factor authentication"),
    (r"\bpassword (change|rotation|refresh|update)\b",
                                  "password rotation password change credential refresh"),
    (r"\bvpn\b",                  "virtual private network remote access"),
    (r"\bremote work\b",          "work from home working remotely"),
    (r"\bwork from home\b",       "remote work working remotely"),
    (r"\bworking remotely\b",     "remote work work from home"),
    (r"\bremote\b",               "work from home"),
    # Data protection
    (r"\bdpia\b",                 "data protection impact assessment"),
    (r"\bdata breach\b",          "incident incident response notification"),
    (r"\bincident response\b",    "data breach notification reporting"),
    (r"\bgdpr\b",                 "data protection privacy"),
    (r"\bdata retention\b",       "record keeping archive"),
    # Document / asset handling
    (r"\bdocument disposal\b",    "secure shredding destruction"),
    (r"\bdocument destruction\b", "shredding disposal"),
    (r"\bshredding\b",            "document disposal destruction"),
    (r"\bclassification\b",       "data labels confidential restricted public"),
    # Training / awareness
    (r"\btraining\b",             "awareness mandatory programme"),
    (r"\bawareness\b",            "training mandatory"),
    # Business continuity
    (r"\bbusiness continuity\b",  "disaster recovery resilience"),
    (r"\bbackup\b",               "recovery restore archive"),
]


def normalise_query(query: str) -> Tuple[str, list]:
    """Return ``(expanded_query, applied_patterns)``.

    ``expanded_query`` is the original query followed by the appended
    extra tokens. ``applied_patterns`` lists the regex patterns that
    fired (useful for tests).
    """
    if not query:
        return query, []
    applied = []
    appended_tokens: list[str] = []
    seen_tokens: set[str] = set()
    for pattern, extras in _EXPANSIONS:
        if re.search(pattern, query, flags=re.IGNORECASE):
            applied.append(pattern)
            for tok in extras.split():
                if tok.lower() not in seen_tokens:
                    appended_tokens.append(tok)
                    seen_tokens.add(tok.lower())
    if not appended_tokens:
        return query, []
    return f"{query} {' '.join(appended_tokens)}", applied
