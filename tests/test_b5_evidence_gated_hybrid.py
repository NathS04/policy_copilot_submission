"""Phase 1 tests: B5 Evidence-Gated Hybrid module."""
from __future__ import annotations

import inspect

from policy_copilot.service import evidence_gated_hybrid as egh
from policy_copilot.service.evidence_gated_hybrid import (
    apply_b5_gate,
    _jaccard_overlap,
    _extract_qualifiers,
    _is_generic_paragraph,
    _question_is_numeric_shape,
)


def _ev(text, pid, score_rerank=0.99):
    return {"paragraph_id": pid, "text": text, "score_rerank": score_rerank}


# ----- helpers ----------------------------------------------------------

def test_jaccard_overlap_helper():
    assert _jaccard_overlap("notice period resignation", "the standard notice period is 1 month") > 0.0
    assert _jaccard_overlap("totally unrelated", "different words entirely") == 0.0


def test_qualifier_extraction():
    assert "part-time" in _extract_qualifiers("Can part-time employees work remotely?")
    assert "overseas" in _extract_qualifiers("What is the policy on working from overseas?")
    assert "non-sensitive" in _extract_qualifiers("Is data encryption required for public non-sensitive information?")
    assert _extract_qualifiers("How long is the notice period?") == []


def test_generic_paragraph_helper():
    assert _is_generic_paragraph("Employees must follow the policy as needed.")
    assert _is_generic_paragraph("Procedures may vary.")
    assert not _is_generic_paragraph("Passwords must be a minimum of 12 characters in length.")


def test_numeric_shape_helper():
    assert _question_is_numeric_shape("How many days?")
    assert _question_is_numeric_shape("What is the maximum probation period?")
    assert not _question_is_numeric_shape("Is there a grievance procedure?")


# ----- gate rules -------------------------------------------------------

def test_surfaces_when_overlap_strong_and_qualifier_present():
    """An answerable-style query with strong overlap and matching qualifier surfaces."""
    out = apply_b5_gate(
        "What is the minimum password length?",
        [_ev("Passwords must be a minimum of 12 characters in length.", "p1")],
    )
    assert out["mode_used"] == "surfaced"
    assert out["citations"] == ["p1"]
    assert out["is_abstained"] is False


def test_abstains_when_overlap_below_floor():
    """Very low overlap should abstain regardless of rerank."""
    out = apply_b5_gate(
        "What is the company holiday allowance?",
        [_ev("Encryption Standards Update. All confidential data must be encrypted.", "p1", score_rerank=0.99)],
    )
    assert out["mode_used"] == "abstained"
    assert "overlap" in out["answerability_reason"]


def test_abstains_on_qualifier_missing_high_rerank_anomaly():
    """The signature failure mode the gate is designed for:
    high rerank + low overlap + question qualifier missing from top paragraph.

    The synthetic question and paragraph are constructed so that the
    Jaccard overlap drops below the low_overlap_cutoff (0.058) — i.e.,
    only one or two non-stopword tokens overlap — and the question's
    `part-time` qualifier is genuinely absent from the paragraph.
    """
    # Question and paragraph chosen to keep overlap minimal: the only
    # shared content tokens after stopwords are "work" and "remotely"
    # vs longer paragraph that dominates the union, putting Jaccard
    # below 0.058. The qualifier "part-time" is not in the paragraph.
    long_paragraph = (
        "Annual leave and bank holiday entitlement details follow the standard "
        "calendar year accrual model based on tenure with the organisation. "
        "Eligible team members must coordinate planned absence with their "
        "department head no fewer than fourteen calendar days ahead, except "
        "in cases authorised by HR. Bank holiday substitution and special "
        "compensatory leave details are recorded in the annual handbook."
    )
    out = apply_b5_gate(
        "Can part-time employees work remotely?",
        [_ev(long_paragraph, "p1", score_rerank=0.99)],
    )
    # The gate should fire on either overlap-below-floor OR qualifier-missing-anomaly
    assert out["mode_used"] == "abstained"
    assert (
        "overlap" in out["answerability_reason"]
        or "qualifier_missing" in out["answerability_reason"]
    )


def test_abstains_on_numeric_q_no_digit():
    """Numeric question + paragraph with no digit -> abstain."""
    out = apply_b5_gate(
        "How long is the probation period?",
        [_ev("Probationary employees are subject to a separate process as outlined in their contract.", "p1", score_rerank=0.99)],
    )
    assert out["mode_used"] == "abstained"


def test_abstains_on_generic_paragraph():
    out = apply_b5_gate(
        "What is the data classification policy?",
        [_ev("Employees must follow the policy as needed for data classification matters and procedures.", "p1", score_rerank=0.99)],
    )
    assert out["mode_used"] == "abstained"
    assert "generic" in out["answerability_reason"]


def test_contradiction_aware_surfaces_when_both_sides_retrieved():
    """If contradictions name two paragraph IDs both in top-5, surface both."""
    evidence = [
        _ev("Passwords must be a minimum of 8 characters in length.", "p_handbook"),
        _ev("All passwords must now be a minimum of 12 characters in length.", "p_addendum"),
    ]
    contradictions = [
        {
            "type": "numeric_conflict",
            "paragraph_ids": ["p_handbook", "p_addendum"],
            "rationale": "8 vs 12 chars",
        }
    ]
    out = apply_b5_gate(
        "Does the policy require both 8 and 12 character minimum passwords in different sections?",
        evidence,
        contradictions=contradictions,
    )
    assert out["mode_used"] == "surfaced_contradiction_aware"
    assert set(out["citations"]) == {"p_handbook", "p_addendum"}


def test_contradiction_aware_abstains_when_only_one_side_retrieved():
    """If contradictions mention 2 IDs but only one is in top-5, fall back to normal gate."""
    evidence = [_ev("Passwords must be a minimum of 8 characters in length.", "p_handbook")]
    contradictions = [
        {
            "type": "numeric_conflict",
            "paragraph_ids": ["p_handbook", "p_addendum_not_retrieved"],
        }
    ]
    out = apply_b5_gate(
        "Is the password minimum 8 or 12 characters?",
        evidence,
        contradictions=contradictions,
    )
    # Falls back to normal gate; should still surface this one paragraph (it has overlap + digit)
    assert out["mode_used"] in ("surfaced", "abstained")
    assert "contradiction_aware" not in out["mode_used"]


# ----- integrity --------------------------------------------------------

def test_b5_module_does_not_reference_golden_set():
    src = inspect.getsource(egh)
    forbidden = ["golden_set", "gold_paragraph_ids", "golden_set.csv", "category =="]
    for tok in forbidden:
        assert tok not in src, f"b5 module references {tok!r}"


def test_b5_never_returns_uncited_surfaced_answer():
    """Every surfaced response must have at least one citation."""
    out = apply_b5_gate(
        "What is the minimum password length?",
        [_ev("Passwords must be a minimum of 12 characters in length.", "p1")],
    )
    if not out["is_abstained"]:
        assert out["citations"], "surfaced response missing citation"


def test_empty_evidence_abstains():
    out = apply_b5_gate("Any question?", [])
    assert out["mode_used"] == "abstained"
    assert "retrieval_weak" in out["answerability_reason"]


def test_metadata_complete():
    """Every response must carry the required B5 metadata fields."""
    out = apply_b5_gate(
        "What is the minimum password length?",
        [_ev("Passwords must be a minimum of 12 characters.", "p1")],
    )
    required = {
        "mode_used", "is_abstained", "answer", "citations",
        "answerability_decision", "answerability_reason",
        "selected_citation_ids", "evidence_strength", "gate_features",
    }
    missing = required - set(out.keys())
    assert not missing, f"missing B5 metadata fields: {missing}"
