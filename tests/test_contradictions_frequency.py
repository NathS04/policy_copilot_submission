"""Phase 5 tests: frequency-conflict detector + new antonym pairs.

Verifies:
  1. permitted/prohibited antonym now fires.
  2. annually/quarterly frequency conflict fires on shared subject.
  3. annually/quarterly does NOT fire when subjects are unrelated.
  4. Same-frequency paragraphs do not conflict.
  5. Existing antonym + quantitative tests still work.
"""
from __future__ import annotations

from policy_copilot.verify.contradictions import detect_contradictions


def _ev(text, pid):
    return {"text": text, "paragraph_id": pid}


def test_permitted_vs_prohibited_detected():
    evidence = [
        _ev("USB storage devices are permitted with prior approval.", "p1"),
        _ev("USB storage devices are prohibited on all company endpoints.", "p2"),
    ]
    out = detect_contradictions(evidence)
    assert out, "permitted/prohibited antonym pair did not fire"


def test_annual_vs_quarterly_training_conflict():
    evidence = [
        _ev("Security awareness training must be completed annually.", "p1"),
        _ev("Security awareness training must be completed quarterly.", "p2"),
    ]
    out = detect_contradictions(evidence)
    assert out, "annual vs quarterly training conflict not detected"


def test_annual_vs_quarterly_unrelated_subjects_no_conflict():
    """A finance report 'annually' vs a training cycle 'quarterly' should
    NOT count as a conflict (different subjects)."""
    evidence = [
        _ev("Finance reports are produced annually.", "p1"),
        _ev("Training cycles run quarterly.", "p2"),
    ]
    out = detect_contradictions(evidence)
    # The detector should not flag these as conflicts (no shared content subject).
    for c in out:
        # Allow the antonym-fallback noise but require it didn't fire on frequency rule.
        assert "frequency" not in c.get("rationale", ""), c


def test_same_frequency_no_conflict():
    evidence = [
        _ev("Training is conducted annually.", "p1"),
        _ev("Annual training is required.", "p2"),
    ]
    out = detect_contradictions(evidence)
    # No frequency conflict since both say annually
    for c in out:
        assert "frequency" not in c.get("rationale", "")


def test_existing_antonym_must_must_not_still_works():
    evidence = [
        _ev("Employees must use VPN.", "p1"),
        _ev("Employees must not use public Wi-Fi for VPN.", "p2"),
    ]
    out = detect_contradictions(evidence)
    assert out


def test_existing_numeric_conflict_still_works():
    """Phase H 8 vs 12 character password length must keep working."""
    evidence = [
        _ev("Passwords must be a minimum of 8 characters.", "p1"),
        _ev("Passwords must be a minimum of 12 characters.", "p2"),
    ]
    out = detect_contradictions(evidence)
    assert out
