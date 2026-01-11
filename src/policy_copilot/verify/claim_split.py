"""
Splits an answer into atomic claims and extracts per-claim citations.
"""
import re
from typing import List, Dict


# pattern to match inline citations like [CITATION: some_id]
_CITATION_RE = re.compile(r'\[CITATION:\s*([^\]]+)\]')
_PLACEHOLDER_RE = re.compile(r'__CITE\d+__')


def split_claims(answer_text: str) -> List[Dict]:
    """
    Splits answer text into sentence-level claims.
    Extracts inline [CITATION: paragraph_id] tags per claim.
    Returns list of dicts: {claim_id, text, citations}
    """
    if not answer_text or answer_text == "INSUFFICIENT_EVIDENCE":
        return []

    # First, find all citation tags and temporarily replace them with placeholders
    # so they don't interfere with sentence splitting
    citations_by_pos = {}
    placeholder_text = answer_text
    for i, m in enumerate(list(_CITATION_RE.finditer(answer_text))):
        placeholder = f"__CITE{i}__"
        citations_by_pos[placeholder] = m.group(1).strip()
        placeholder_text = placeholder_text.replace(m.group(0), placeholder, 1)

    # split on sentence boundaries (period, exclamation, question mark)
    # followed by whitespace
    raw_sentences = re.split(r'(?<=[.!?])\s+', placeholder_text.strip())

    # merge fragments that are purely placeholders back into the previous sentence
    merged = []
    for sent in raw_sentences:
        stripped = _PLACEHOLDER_RE.sub('', sent).strip()
        if not stripped and merged:
            # this fragment has only placeholders — merge into previous
            merged[-1] = merged[-1] + " " + sent
        else:
            merged.append(sent)

    claims = []
    claim_idx = 0
    for sent in merged:
        sent = sent.strip()
        if not sent:
            continue

        # extract citations from placeholders in this sentence
        found_citations = []
        for placeholder, cid in citations_by_pos.items():
            if placeholder in sent:
                found_citations.append(cid)
                sent = sent.replace(placeholder, "")

        # clean up extra whitespace
        clean_text = re.sub(r'\s+', ' ', sent).strip()

        if not clean_text or len(clean_text) < 3:
            continue

        # Skip numeric-only fragments like "13." or "9)" that cause false abstention
        if re.match(r"^\s*\d+\s*[\.)]?\s*$", clean_text):
            continue

        claims.append({
            "claim_id": f"c{claim_idx:04d}",
            "text": clean_text,
            "citations": found_citations,
        })
        claim_idx += 1

    return claims


def extract_all_citations(answer_text: str) -> List[str]:
    """
    Extracts all [CITATION: ...] paragraph_ids from the full answer text.
    Returns deduplicated list preserving order.
    """
    found = _CITATION_RE.findall(answer_text or "")
    seen = set()
    result = []
    for c in found:
        c = c.strip()
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result
