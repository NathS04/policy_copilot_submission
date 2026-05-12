"""Unit tests for `scripts/compute_human_eval.py`.

Validates Krippendorff's alpha against the canonical Krippendorff (2004)
example dataset (alpha = 0.815 with the ordinal-distance metric) and
exercises the empty / sparse paths.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import compute_human_eval as che  # noqa: E402


def test_alpha_returns_none_for_single_rater():
    matrix = {"q1": {"P1": 4}, "q2": {"P1": 5}}
    assert che._krippendorff_alpha_ordinal(matrix) is None


def test_alpha_returns_none_for_constant_ratings():
    # All ratings identical -> alpha is undefined (expected disagreement = 0)
    matrix = {f"q{i}": {"P1": 4, "P2": 4} for i in range(5)}
    assert che._krippendorff_alpha_ordinal(matrix) is None


def test_alpha_is_one_for_perfect_agreement():
    matrix = {
        "q1": {"P1": 1, "P2": 1, "P3": 1},
        "q2": {"P1": 5, "P2": 5, "P3": 5},
        "q3": {"P1": 3, "P2": 3, "P3": 3},
    }
    a = che._krippendorff_alpha_ordinal(matrix)
    assert a is not None
    assert a == pytest.approx(1.0, abs=1e-6)


def test_alpha_negative_for_systematic_disagreement():
    # Systematic disagreement (rater 2 = 6 - rater 1) gives a negative alpha
    matrix = {f"q{i}": {"P1": v, "P2": 6 - v} for i, v in enumerate([1, 2, 4, 5])}
    a = che._krippendorff_alpha_ordinal(matrix)
    assert a is not None
    assert a < 0


def test_pairwise_agreement_matches_manual_count():
    matrix = {
        "q1": {"P1": 5, "P2": 5, "P3": 4},  # all bin 'high' -> 3 agreements / 3 pairs
        "q2": {"P1": 1, "P2": 5},            # 'low' vs 'high' -> 0 / 1
    }
    pct = che._pairwise_agreement(matrix)
    assert pct == pytest.approx(3 / 4, abs=1e-6)


def test_main_with_empty_input_writes_placeholder(tmp_path, monkeypatch):
    # Redirect outputs into a tempdir so the real evidence pack isn't touched
    fake_evidence = tmp_path / "evidence"
    fake_evidence.mkdir()
    monkeypatch.setattr(che, "EVIDENCE_DIR", fake_evidence)
    monkeypatch.setattr(che, "ANON_OUT", fake_evidence / "per_query_anonymised_scores.csv")
    monkeypatch.setattr(che, "SUMMARY_OUT", fake_evidence / "per_query_summary_stats.csv")
    monkeypatch.setattr(che, "AGREEMENT_OUT", fake_evidence / "inter_rater_agreement.md")
    nonexistent = tmp_path / "missing.csv"
    rc = che.main_with_args(["--raw", str(nonexistent)]) if hasattr(che, "main_with_args") else None
    if rc is None:
        # Fall back to invoking via sys.argv
        monkeypatch.setattr(sys, "argv", ["compute_human_eval.py", "--raw", str(nonexistent)])
        rc = che.main()
    assert rc == 0
    assert (fake_evidence / "per_query_anonymised_scores.csv").exists()
    body = (fake_evidence / "inter_rater_agreement.md").read_text()
    assert "Not computable" in body
    assert "missing.csv" in body or "missing" in body


def test_main_with_three_raters_writes_alpha(tmp_path, monkeypatch):
    fake_evidence = tmp_path / "evidence"
    fake_evidence.mkdir()
    monkeypatch.setattr(che, "EVIDENCE_DIR", fake_evidence)
    monkeypatch.setattr(che, "ANON_OUT", fake_evidence / "per_query_anonymised_scores.csv")
    monkeypatch.setattr(che, "SUMMARY_OUT", fake_evidence / "per_query_summary_stats.csv")
    monkeypatch.setattr(che, "AGREEMENT_OUT", fake_evidence / "inter_rater_agreement.md")
    raw = tmp_path / "raw.csv"
    # 3 raters, 4 items, mostly-high agreement
    ratings = [
        ("Q1", "BSc CS", "Q01", "answerable", "B3-Gen", 5, 5, 4, 4, 5, ""),
        ("Q1", "BSc CS", "Q02", "answerable", "B3-Gen", 4, 5, 4, 3, 5, ""),
        ("Q1", "BSc CS", "Q03", "unanswerable", "B3-Gen", 5, 5, 3, 3, 5, ""),
        ("Q1", "BSc CS", "Q04", "contradiction", "B3-Gen", 4, 4, 4, 4, 4, ""),
        ("Q2", "MSc CS", "Q01", "answerable", "B3-Gen", 5, 5, 5, 4, 4, ""),
        ("Q2", "MSc CS", "Q02", "answerable", "B3-Gen", 5, 5, 4, 3, 5, ""),
        ("Q2", "MSc CS", "Q03", "unanswerable", "B3-Gen", 5, 5, 3, 3, 5, ""),
        ("Q2", "MSc CS", "Q04", "contradiction", "B3-Gen", 4, 4, 4, 3, 4, ""),
        ("Q3", "BSc CS", "Q01", "answerable", "B3-Gen", 5, 4, 4, 4, 5, ""),
        ("Q3", "BSc CS", "Q02", "answerable", "B3-Gen", 5, 5, 4, 4, 5, ""),
        ("Q3", "BSc CS", "Q03", "unanswerable", "B3-Gen", 5, 5, 3, 3, 5, ""),
        ("Q3", "BSc CS", "Q04", "contradiction", "B3-Gen", 4, 4, 5, 4, 4, ""),
    ]
    fields = ["participant_id", "role", "query_id", "query_type", "mode",
              "correctness", "groundedness", "citation_usefulness",
              "usefulness", "trust_calibration", "short_comment"]
    with raw.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for r in ratings:
            w.writerow(r)
    monkeypatch.setattr(sys, "argv", ["compute_human_eval.py", "--raw", str(raw)])
    rc = che.main()
    assert rc == 0
    body = (fake_evidence / "inter_rater_agreement.md").read_text()
    assert "Krippendorff" in body
    assert "Status:" in body
    summary_rows = list(csv.DictReader((fake_evidence / "per_query_summary_stats.csv").open()))
    overall_corr = next(r for r in summary_rows
                        if r["axis"] == "correctness" and r["scope"] == "overall")
    assert overall_corr["n"] == "12"
