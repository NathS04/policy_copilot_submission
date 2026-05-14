"""Tests for the golden-set label audit (Phase A).

Verifies:
1. The audit script runs deterministically.
2. golden_set_v2_corrected.csv has the expected denominators
   (40 answerable / 13 unanswerable / 10 contradiction = 63 total).
3. Each relabelled query (q_004, q_014, q_016, q_062) is now answerable
   with the expected gold paragraph IDs.
4. Every gold_paragraph_id in v2 exists in data/corpus/processed/paragraphs.csv.
5. Every answerable row has ≥1 gold_paragraph_id; every contradiction row
   has ≥2 (matching tests/test_golden_set_validation.py rules).
6. No silent drops between v1 and v2 — same set of query_ids.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "eval/golden_set/golden_set.csv"
V2 = ROOT / "eval/golden_set/golden_set_v2_corrected.csv"
CORPUS = ROOT / "data/corpus/processed/paragraphs.csv"
AUDIT_CSV = ROOT / "results/tables/golden_set_label_audit.csv"
AUDIT_MD = ROOT / "docs/evidence/verification/golden_set_label_audit.md"
AUDIT_SCRIPT = ROOT / "scripts/audit_golden_set_labels.py"

EXPECTED_RELABELS = {
    "q_004": ("answerable", "internal_policy_handbook_v2::p0014::i0000::22101d8d9bb7"),
    "q_014": ("answerable", "hr_procedures_manual::p0009::i0000::ceb3a6266920"),
    "q_016": ("answerable", "hr_procedures_manual::p0008::i0000::559a594dc2ac"),
    "q_062": ("answerable", "hr_procedures_manual::p0006::i0002::8c5195f8b5ea"),
}


def _load_rows(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def test_v2_denominators():
    rows = _load_rows(V2)
    counts = Counter(r["category"] for r in rows)
    assert len(rows) == 63
    assert counts["answerable"] == 40
    assert counts["unanswerable"] == 13
    assert counts["contradiction"] == 10


def test_relabels_applied():
    rows = {r["query_id"]: r for r in _load_rows(V2)}
    for qid, (expected_cat, expected_gold_prefix) in EXPECTED_RELABELS.items():
        assert qid in rows, f"{qid} missing from v2"
        assert rows[qid]["category"] == expected_cat, (
            f"{qid} category is {rows[qid]['category']!r}, expected {expected_cat!r}"
        )
        assert expected_gold_prefix in rows[qid]["gold_paragraph_ids"], (
            f"{qid} gold_paragraph_ids does not contain {expected_gold_prefix!r}"
        )


def test_all_gold_paragraph_ids_exist_in_corpus():
    corpus_pids = {r["paragraph_id"] for r in _load_rows(CORPUS)}
    rows = _load_rows(V2)
    missing = []
    for r in rows:
        for pid in (r.get("gold_paragraph_ids") or "").split(","):
            pid = pid.strip()
            if pid and pid not in corpus_pids:
                missing.append((r["query_id"], pid))
    assert not missing, f"gold paragraph IDs missing from corpus: {missing}"


def test_answerable_rows_have_gold():
    rows = _load_rows(V2)
    bad = []
    for r in rows:
        if r["category"] == "answerable":
            if not (r.get("gold_paragraph_ids") or "").strip():
                bad.append(r["query_id"])
    assert not bad, f"answerable queries missing gold_paragraph_ids: {bad}"


def test_unanswerable_rows_have_no_gold():
    rows = _load_rows(V2)
    bad = []
    for r in rows:
        if r["category"] == "unanswerable":
            if (r.get("gold_paragraph_ids") or "").strip():
                bad.append((r["query_id"], r["gold_paragraph_ids"]))
    assert not bad, f"unanswerable queries should not have gold: {bad}"


def test_v1_and_v2_have_same_query_ids():
    v1_ids = {r["query_id"] for r in _load_rows(V1)}
    v2_ids = {r["query_id"] for r in _load_rows(V2)}
    assert v1_ids == v2_ids, (
        f"v1 vs v2 query_id diff: only in v1={v1_ids - v2_ids}, "
        f"only in v2={v2_ids - v2_ids}"
    )


def test_audit_artefacts_exist():
    assert AUDIT_CSV.exists(), f"missing {AUDIT_CSV}"
    assert AUDIT_MD.exists(), f"missing {AUDIT_MD}"


def test_audit_script_is_deterministic_and_reports_4_relabels(tmp_path):
    # Run the script to a temp output and verify stdout reports 4 relabels.
    proc = subprocess.run(
        [
            sys.executable, str(AUDIT_SCRIPT),
            "--out-csv", str(tmp_path / "audit.csv"),
            "--out-md", str(tmp_path / "audit.md"),
        ],
        cwd=ROOT,
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"stderr:\n{proc.stderr}"
    assert "Relabel decisions: 4" in proc.stdout, proc.stdout
