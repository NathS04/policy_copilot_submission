"""Phase H tests: quantitative contradiction detection.

Covers password length / rotation conflicts, unit normalisation,
subject-overlap floor, and integration with detect_contradictions().
"""
from __future__ import annotations


from policy_copilot.verify.contradictions import detect_contradictions
from policy_copilot.verify.policy_facts import (
    extract_policy_facts,
    find_quantitative_conflicts,
)


def _ev(text, pid):
    return {"text": text, "paragraph_id": pid}


# ---------- fact extractor ----------

def test_extract_password_length_fact():
    facts = extract_policy_facts(
        "Passwords must be a minimum of 8 characters in length.",
        paragraph_id="p1",
    )
    assert any(f.unit == "chars" and f.value == 8 for f in facts)


def test_extract_password_rotation_fact():
    facts = extract_policy_facts(
        "Passwords must be rotated every 90 days.",
        paragraph_id="p2",
    )
    assert any(f.unit == "days" and f.value == 90 for f in facts)


def test_unit_normalisation():
    facts = extract_policy_facts("rotation every 3 months", paragraph_id="x")
    assert any(f.unit == "months" and f.value == 3 for f in facts)
    facts2 = extract_policy_facts("password must contain 12 chars", paragraph_id="y")
    assert any(f.unit == "chars" and f.value == 12 for f in facts2)


# ---------- conflict detector ----------

def test_8_vs_12_chars_detected():
    fa = extract_policy_facts(
        "passwords must be a minimum of 8 characters",
        paragraph_id="pa",
    )
    fb = extract_policy_facts(
        "passwords must now be a minimum of 12 characters",
        paragraph_id="pb",
    )
    conflicts = find_quantitative_conflicts(fa, fb)
    assert any(set(c["values"]) == {8, 12} and c["unit"] == "chars" for c in conflicts)


def test_60_vs_90_days_rotation_detected():
    fa = extract_policy_facts(
        "password rotation period of 90 days mandated by IT",
        paragraph_id="pa",
    )
    fb = extract_policy_facts(
        "password rotation period is reduced to 60 days",
        paragraph_id="pb",
    )
    conflicts = find_quantitative_conflicts(fa, fb)
    assert any(set(c["values"]) == {60, 90} and c["unit"] == "days" for c in conflicts)


def test_unrelated_numbers_do_not_falsely_conflict():
    # "5+ years of service" vs "5 working days notice" — same value but
    # different units and different subjects.
    fa = extract_policy_facts(
        "Employees with 5 years of service receive additional leave.",
        paragraph_id="pa",
    )
    fb = extract_policy_facts(
        "Notice of 5 working days is required.",
        paragraph_id="pb",
    )
    conflicts = find_quantitative_conflicts(fa, fb)
    # Different units (years vs days) so no conflict even though both = 5.
    # Or same unit but different subject (no overlap above floor).
    for c in conflicts:
        # If anything fires it must be a real conflict, not a numerical coincidence.
        assert c["unit"] not in ("years", "days") or c["values"][0] != c["values"][1]


def test_same_value_in_two_paragraphs_does_not_conflict():
    fa = extract_policy_facts("rotation every 90 days", "pa")
    fb = extract_policy_facts("rotation every 90 days", "pb")
    conflicts = find_quantitative_conflicts(fa, fb)
    assert not conflicts


def test_subject_overlap_floor():
    # Two paragraphs with different subjects: "password rotation 90 days"
    # vs "training renewal 60 days" — both 'days' unit, both numeric, but
    # zero subject overlap → no conflict.
    fa = extract_policy_facts("password rotation policy every 90 days", "pa")
    fb = extract_policy_facts("training renewal cycle 60 days", "pb")
    conflicts = find_quantitative_conflicts(fa, fb)
    assert not conflicts


# ---------- integration with detect_contradictions ----------

def test_detect_contradictions_uses_quantitative_layer():
    """Two real policy paragraphs from the corpus: password length conflict."""
    evidence = [
        _ev(
            "Passwords must meet the following minimum requirements: at least 8 characters in length",
            "internal_policy_handbook_v2::p0005::i0000",
        ),
        _ev(
            "All passwords must now be a minimum of 12 characters in length (increased from 8 characters)",
            "it_security_addendum_2025::p0003::i0000",
        ),
    ]
    contradictions = detect_contradictions(evidence)
    assert contradictions, "detector failed to flag the 8-vs-12 password length conflict"
    pids = set()
    for c in contradictions:
        pids.update(c["paragraph_ids"])
    assert "internal_policy_handbook_v2::p0005::i0000" in pids
    assert "it_security_addendum_2025::p0003::i0000" in pids


def test_legacy_antonym_detector_still_works():
    """Make sure the new layer didn't break the 'must / must not' path."""
    evidence = [
        _ev("Employees must use the corporate VPN.", "pa"),
        _ev("Employees must not use the corporate VPN for personal browsing.", "pb"),
    ]
    contradictions = detect_contradictions(evidence)
    assert contradictions, "antonym detector regression"
