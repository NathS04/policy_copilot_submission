"""Golden-set label audit.

Scans the golden set against the corpus to flag potential mislabels:

- unanswerable queries whose terms strongly hit a corpus paragraph
- answerable queries with empty or invalid gold_paragraph_ids
- contradiction queries with fewer than 2 evidence paragraphs available
- gold_paragraph_ids referencing paragraphs that no longer exist

Outputs:
  results/tables/golden_set_label_audit.csv
  docs/evidence/verification/golden_set_label_audit.md

No LLM calls. No mutation of the original golden set. The corrected
version is written separately to eval/golden_set/golden_set_v2_corrected.csv
based on the audit decisions (this script does not auto-rewrite labels).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path


STOPWORDS = {
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

WORD_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [t for t in WORD_RE.findall(text.lower()) if t not in STOPWORDS]


def load_corpus(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def load_golden(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def score_paragraph_against_query(query_tokens: set[str], para_text: str) -> tuple[float, list[str]]:
    """Return (jaccard-style score, matched terms)."""
    para_tokens = set(tokenize(para_text))
    if not query_tokens or not para_tokens:
        return 0.0, []
    matched = sorted(query_tokens & para_tokens)
    union = query_tokens | para_tokens
    return len(matched) / len(union), matched


def top_candidates(query: str, corpus: list[dict], top_n: int = 5) -> list[dict]:
    q_tokens = set(tokenize(query))
    scored = []
    for para in corpus:
        score, matched = score_paragraph_against_query(q_tokens, para["text"])
        if score > 0 and matched:
            scored.append({
                "paragraph_id": para["paragraph_id"],
                "doc_id": para["doc_id"],
                "score": round(score, 4),
                "matched_terms": ",".join(matched[:5]),
                "snippet": para["text"][:140].replace("\n", " ") + ("..." if len(para["text"]) > 140 else ""),
            })
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_n]


# Suspicion threshold: an unanswerable query with a candidate score above
# this on the corpus is flagged for human review. Tuned on the synthetic
# corpus: real mislabels (q_014, q_016, q_062) all score >= 0.10 on at
# least one paragraph.
SUSPICION_THRESHOLD = 0.10


def audit_row(row: dict, corpus: list[dict], corpus_pid_set: set[str]) -> dict:
    query_id = row["query_id"]
    category = row["category"]
    question = row["question"]
    gold_ids = [g.strip() for g in (row.get("gold_paragraph_ids") or "").split(",") if g.strip()]

    candidates = top_candidates(question, corpus, top_n=5)
    top_score = candidates[0]["score"] if candidates else 0.0
    top_ids = [c["paragraph_id"] for c in candidates]

    flags = []
    suggested_action = "keep_as_is"
    rationale = ""

    # Flag 1: gold paragraphs that don't exist in corpus.
    missing_golds = [g for g in gold_ids if g not in corpus_pid_set]
    if missing_golds:
        flags.append(f"missing_gold_paragraphs:{','.join(missing_golds)}")

    # Flag 2: answerable with no gold_paragraph_ids.
    if category == "answerable" and not gold_ids:
        flags.append("answerable_with_no_gold")
        suggested_action = "add_gold_or_relabel"
        rationale = "answerable rows must list ≥1 gold_paragraph_id"

    # Flag 3: unanswerable with a strong candidate hit in the corpus.
    if category == "unanswerable" and top_score >= SUSPICION_THRESHOLD:
        flags.append(f"unanswerable_but_corpus_hit:score={top_score:.3f}")
        suggested_action = "review_for_relabel_to_answerable"
        rationale = f"Top candidate {top_ids[0]} score {top_score:.3f} suggests the corpus may answer this."

    # Flag 4: contradiction with fewer than 2 candidate paragraphs available.
    if category == "contradiction" and len([c for c in candidates if c["score"] >= 0.05]) < 2:
        flags.append("contradiction_with_lt_2_evidence_candidates")
        suggested_action = "review_contradiction_evidence"
        rationale = "Fewer than 2 candidate paragraphs scored above 0.05 — contradiction may be unobservable."

    return {
        "query_id": query_id,
        "question": question,
        "current_category": category,
        "current_gold_paragraph_ids": ",".join(gold_ids),
        "top_candidate_paragraph_ids": ",".join(top_ids),
        "top_candidate_score": round(top_score, 4),
        "top_candidate_terms": candidates[0]["matched_terms"] if candidates else "",
        "top_candidate_snippet": candidates[0]["snippet"] if candidates else "",
        "flags": "|".join(flags) if flags else "ok",
        "suggested_action": suggested_action,
        "rationale": rationale,
    }


def write_markdown_summary(
    audit_rows: list[dict],
    out_path: Path,
    decisions: dict[str, dict],
) -> None:
    flagged = [r for r in audit_rows if r["flags"] != "ok"]
    relabels = [(qid, d) for qid, d in decisions.items() if d.get("relabel")]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        f.write("# Golden-Set Label Audit\n\n")
        f.write("This audit was produced by `scripts/audit_golden_set_labels.py` to "
                "flag possible mislabels in the original golden set "
                "(`eval/golden_set/golden_set.csv`). No LLM calls were used — the "
                "audit relies on stopword-stripped token overlap (Jaccard) between "
                "each query and every corpus paragraph.\n\n")
        f.write(f"- Total queries audited: **{len(audit_rows)}**\n")
        f.write(f"- Queries flagged for review: **{len(flagged)}**\n")
        f.write(f"- Queries relabelled in `golden_set_v2_corrected.csv`: **{len(relabels)}**\n\n")
        f.write("## Methodology\n\n"
                "1. Tokenise each query and each paragraph with case-folding and English stopword removal.\n"
                "2. For each query, score every paragraph by Jaccard token overlap.\n"
                "3. Flag any *unanswerable* query whose top candidate scores ≥ "
                f"{SUSPICION_THRESHOLD}, any *answerable* query missing gold IDs, "
                "and any *contradiction* query with fewer than two candidate "
                "paragraphs above 0.05.\n"
                "4. Read the flagged paragraphs by hand; relabel only if the "
                "corpus genuinely answers the question.\n\n")
        f.write("## Relabel decisions\n\n")
        if relabels:
            f.write("| Query | Old | New | Gold added | Evidence |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for qid, d in relabels:
                f.write(f"| {qid} | {d['old_category']} | {d['new_category']} | "
                        f"`{d.get('new_gold_paragraph_ids','')}` | {d.get('evidence','')} |\n")
            f.write("\n")
        else:
            f.write("No relabels were applied.\n\n")
        f.write("## All flagged queries\n\n")
        f.write("Listed verbatim from `results/tables/golden_set_label_audit.csv`. "
                "Decisions are inline.\n\n")
        for r in flagged:
            qid = r["query_id"]
            d = decisions.get(qid, {})
            f.write(f"### {qid} — {r['question']}\n\n")
            f.write(f"- **Original**: `{r['current_category']}` / gold: `{r['current_gold_paragraph_ids'] or '(none)'}`\n")
            f.write(f"- **Top candidate**: `{r['top_candidate_paragraph_ids'].split(',')[0] if r['top_candidate_paragraph_ids'] else '(none)'}` "
                    f"(score {r['top_candidate_score']}, terms: {r['top_candidate_terms']})\n")
            f.write(f"- **Flags**: {r['flags']}\n")
            if d.get("relabel"):
                f.write(f"- **Decision**: relabel to `{d['new_category']}` with gold "
                        f"`{d.get('new_gold_paragraph_ids','')}`. {d.get('evidence','')}\n")
            else:
                f.write(f"- **Decision**: {d.get('decision', 'keep as-is')}. "
                        f"{d.get('evidence','')}\n")
            f.write("\n")


def main() -> int:
    here = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-set", type=Path,
                        default=here / "eval/golden_set/golden_set.csv")
    parser.add_argument("--corpus", type=Path,
                        default=here / "data/corpus/processed/paragraphs.csv")
    parser.add_argument("--out-csv", type=Path,
                        default=here / "results/tables/golden_set_label_audit.csv")
    parser.add_argument("--out-md", type=Path,
                        default=here / "docs/evidence/verification/golden_set_label_audit.md")
    args = parser.parse_args()

    if not args.golden_set.exists():
        print(f"ERROR: missing {args.golden_set}", file=sys.stderr)
        return 2
    if not args.corpus.exists():
        print(f"ERROR: missing {args.corpus}", file=sys.stderr)
        return 2

    golden = load_golden(args.golden_set)
    corpus = load_corpus(args.corpus)
    corpus_pid_set = {p["paragraph_id"] for p in corpus}

    audit_rows = [audit_row(r, corpus, corpus_pid_set) for r in golden]

    # Manual relabel decisions for the three confirmed-by-corpus mislabels.
    decisions = {
        "q_014": {
            "relabel": True,
            "old_category": "unanswerable",
            "new_category": "answerable",
            "new_gold_paragraph_ids": "hr_procedures_manual::p0009::i0000::ceb3a6266920",
            "new_gold_doc_ids": "hr_procedures_manual",
            "evidence": "HR Procedures Manual paragraph p0009::i0000 states 'The standard notice period is: 1 month for employees below senior management, ...'.",
        },
        "q_016": {
            "relabel": True,
            "old_category": "unanswerable",
            "new_category": "answerable",
            "new_gold_paragraph_ids": "hr_procedures_manual::p0008::i0000::559a594dc2ac,hr_procedures_manual::p0008::i0001::cedb99dfaf25,hr_procedures_manual::p0008::i0002::01ccd9d70161",
            "new_gold_doc_ids": "hr_procedures_manual",
            "evidence": "HR Procedures Manual §7 'Grievance Procedure' (paragraphs p0008::i0000 through p0008::i0002) sets out the formal procedure, hearing, appeal and non-retaliation policy.",
        },
        "q_062": {
            "relabel": True,
            "old_category": "unanswerable",
            "new_category": "answerable",
            "new_gold_paragraph_ids": "hr_procedures_manual::p0006::i0002::8c5195f8b5ea",
            "new_gold_doc_ids": "hr_procedures_manual",
            "evidence": "HR Procedures Manual paragraph p0006::i0002 explicitly states: 'Requests for unpaid leave, sabbaticals, or career breaks must be submitted to HR at least 3 months in advance. Approval is at the discretion of the department head and HR Director.' — the company does offer sabbatical leave, by application.",
        },
        "q_004": {
            "relabel": True,
            "old_category": "unanswerable",
            "new_category": "answerable",
            "new_gold_paragraph_ids": "internal_policy_handbook_v2::p0014::i0000::22101d8d9bb7,internal_policy_handbook_v2::p0014::i0001::57e8f6f4cafc,internal_policy_handbook_v2::p0014::i0002::051345293182,internal_policy_handbook_v2::p0014::i0003::c79e6cb648ff",
            "new_gold_doc_ids": "internal_policy_handbook_v2",
            "evidence": "Internal Policy Handbook §13 'Bring Your Own Device (BYOD) Policy' (paragraphs p0014::i0000-i0003) explicitly states 'Employees may use personal devices (smartphones, tablets, laptops) for work purposes subject to the conditions in this section' and sets out the BYOD enrolment, MDM, secure-container, and reporting requirements.",
        },
    }

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="") as f:
        fields = [
            "query_id", "question", "current_category",
            "current_gold_paragraph_ids", "top_candidate_paragraph_ids",
            "top_candidate_score", "top_candidate_terms",
            "top_candidate_snippet", "flags", "suggested_action", "rationale",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in audit_rows:
            w.writerow({k: r.get(k, "") for k in fields})

    write_markdown_summary(audit_rows, args.out_md, decisions)

    # Console summary.
    flag_counts: Counter[str] = Counter()
    for r in audit_rows:
        if r["flags"] != "ok":
            for f_ in r["flags"].split("|"):
                flag_counts[f_.split(":")[0]] += 1
    print(f"Audited {len(audit_rows)} queries.")
    print(f"Flag counts: {dict(flag_counts)}")
    print(f"Relabel decisions: {len([d for d in decisions.values() if d.get('relabel')])}")
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
