#!/usr/bin/env python3
"""
Auto-labels gold_paragraph_ids in golden_set.csv using retrieval + content matching.
For the synthetic corpus, we can map queries to paragraphs deterministically.
"""
import csv
import json
import sys
from pathlib import Path

# Mapping: query_id -> list of paragraph IDs (manually curated based on corpus content)
# These are the paragraph IDs from the actual ingested corpus.
# Built by inspecting paragraphs.jsonl and matching to golden set questions.

def _load_paragraph_index(jsonl_path: str) -> dict[str, dict]:
    """Load paragraph ID -> full record mapping."""
    pindex = {}
    with open(jsonl_path) as f:
        for line in f:
            p = json.loads(line)
            pindex[p["paragraph_id"]] = p
    return pindex


def _find_best_pids(query_id: str, question: str, category: str,
                     pindex: dict) -> tuple[list[str], list[str]]:
    """Return (gold_paragraph_ids, gold_doc_ids) for a query.
    Uses keyword matching against paragraph text.
    Returns empty lists for unanswerable queries.
    """
    if category == "unanswerable":
        return [], []

    question_lower = question.lower()
    scored = []

    for pid, rec in pindex.items():
        text_lower = rec["text"].lower()
        # simple keyword overlap score
        q_words = set(question_lower.split())
        t_words = set(text_lower.split())
        overlap = len(q_words & t_words)
        # bonus for key terms
        bonus = 0
        key_terms = _extract_key_terms(query_id, question_lower)
        for term in key_terms:
            if term in text_lower:
                bonus += 5
        scored.append((pid, rec["doc_id"], overlap + bonus))

    scored.sort(key=lambda x: -x[2])

    if category == "answerable":
        # Take top 1-2 paragraphs with score > threshold
        top = [s for s in scored[:3] if s[2] > 3]
        if not top:
            top = scored[:1]  # fallback: take best
        pids = [s[0] for s in top[:2]]
        dids = list(set(s[1] for s in top[:2]))
        return pids, dids

    elif category == "contradiction":
        # Need >=2 paragraphs from different documents or sections
        # Find contradicting pairs
        pairs = _find_contradiction_pair(query_id, question_lower, pindex)
        if pairs:
            pids = [p[0] for p in pairs]
            dids = list(set(p[1] for p in pairs))
            return pids, dids
        # Fallback: top 2 from different docs
        top = scored[:5]
        if len(top) >= 2:
            pids = [top[0][0], top[1][0]]
            dids = list(set([top[0][1], top[1][1]]))
            return pids, dids
        return [scored[0][0]], [scored[0][1]] if scored else ([], [])

    return [], []


def _extract_key_terms(query_id: str, question: str) -> list[str]:
    """Extract domain-specific key terms from the question."""
    terms = []
    keyword_map = {
        "remote": ["remote", "remotely", "work from home"],
        "password": ["password", "passwords"],
        "encryption": ["encrypt", "encryption"],
        "usb": ["usb", "removable media"],
        "visitor": ["visitor", "visitors"],
        "training": ["training", "awareness"],
        "backup": ["backup", "back up"],
        "access": ["access control", "authorisation", "authorization"],
        "breach": ["breach", "incident"],
        "server": ["server room", "data centre"],
        "clean desk": ["clean desk"],
        "retention": ["retention", "retained"],
        "email": ["email", "e-mail"],
        "software": ["software", "install"],
        "mfa": ["multi-factor", "mfa", "authentication"],
        "vpn": ["vpn"],
        "social media": ["social media"],
        "disposal": ["disposal", "dispose", "shred"],
        "cloud": ["cloud", "storage"],
        "lockout": ["lockout", "failed login", "login attempts"],
        "data sharing": ["sharing", "share data", "externally"],
        "compliance": ["compliance", "non-compliance", "consequences"],
        "classification": ["classification", "classify", "classified"],
        "physical security": ["physical security", "badge", "cctv"],
        "personal device": ["personal device", "byod", "personal devices"],
        "working hours": ["working hours", "core hours"],
        "equipment": ["equipment", "laptop", "monitor"],
    }
    for key, triggers in keyword_map.items():
        for t in triggers:
            if t in question:
                terms.append(key)
                break
    return terms


# Contradiction mapping: query_id -> (handbook_section_keyword, addendum_section_keyword)
CONTRADICTION_MAP = {
    "q_051": ("remote work policy", "staff attendance"),
    "q_052": ("encryption", "encryption standards"),
    "q_053": ("personal device", "personal devices"),
    "q_054": ("password", "enhanced password"),
    "q_055": ("public wi-fi", "network access"),
    "q_056": ("usb", "usb and removable"),
    "q_057": ("visitor", "visitor access"),
    "q_058": ("training", "training frequency"),
    "q_059": ("sharing data externally", "data sharing approval"),
    "q_060": ("minimum password length", "minimum password length"),
}


def _find_contradiction_pair(query_id: str, question: str,
                              pindex: dict) -> list[tuple[str, str]]:
    """Find contradicting paragraph pair for a contradiction query."""
    if query_id not in CONTRADICTION_MAP:
        return []

    kw_handbook, kw_addendum = CONTRADICTION_MAP[query_id]

    handbook_pid = None
    addendum_pid = None

    for pid, rec in pindex.items():
        text_lower = rec["text"].lower()
        doc = rec["doc_id"]
        if doc.startswith("internal_policy") and kw_handbook in text_lower and not handbook_pid:
            handbook_pid = (pid, doc)
        elif doc.startswith("it_security") and kw_addendum in text_lower and not addendum_pid:
            addendum_pid = (pid, doc)

    result = []
    if handbook_pid:
        result.append(handbook_pid)
    if addendum_pid:
        result.append(addendum_pid)
    return result


def main():
    gs_path = Path("eval/golden_set/golden_set.csv")
    jsonl_path = Path("data/corpus/processed/paragraphs.jsonl")

    if not gs_path.exists():
        print(f"[!] {gs_path} not found")
        sys.exit(1)
    if not jsonl_path.exists():
        print(f"[!] {jsonl_path} not found — run ingest first")
        sys.exit(1)

    pindex = _load_paragraph_index(str(jsonl_path))
    print(f"[+] Loaded {len(pindex)} paragraphs")

    rows = []
    with open(gs_path) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    for row in rows:
        qid = row["query_id"]
        question = row["question"]
        category = row["category"]
        existing = row.get("gold_paragraph_ids", "").strip()

        if category == "unanswerable":
            row["gold_paragraph_ids"] = ""
            row["gold_doc_ids"] = ""
            continue

        if existing:
            # Already labelled (e.g., q_001-q_003 that had doc_handbook_v1)
            # Re-label with actual paragraph IDs from new corpus
            pass

        pids, dids = _find_best_pids(qid, question, category, pindex)

        if pids:
            row["gold_paragraph_ids"] = ",".join(pids)
            row["gold_doc_ids"] = ",".join(dids)
            updated += 1
            status = "✓" if (category == "contradiction" and len(pids) >= 2) or category == "answerable" else "⚠"
            print(f"  [{status}] {qid} ({category}): {len(pids)} gold IDs")
        else:
            print(f"  [!] {qid}: no matching paragraphs found")

    # Write back
    with open(gs_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[✓] Updated {updated} rows in {gs_path}")
    print("    Next: python scripts/validate_golden_set.py")


if __name__ == "__main__":
    main()
