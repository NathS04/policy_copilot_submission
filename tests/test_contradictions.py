"""
Tests for contradiction detection.
"""
from policy_copilot.verify.contradictions import (
    detect_contradictions, apply_contradiction_policy
)


class TestContradictionDetection:
    def test_must_vs_must_not(self):
        """'must' vs 'must not' should trigger contradiction."""
        evidence = [
            {"paragraph_id": "p1", "text": "Users must enable two-factor authentication."},
            {"paragraph_id": "p2", "text": "Users must not enable two-factor authentication for guest accounts."},
        ]
        contradictions = detect_contradictions(evidence)
        assert len(contradictions) >= 1
        assert contradictions[0]["type"] == "contradiction"
        assert set(contradictions[0]["paragraph_ids"]) == {"p1", "p2"}

    def test_allowed_vs_forbidden(self):
        """'allowed' vs 'forbidden' should trigger contradiction."""
        evidence = [
            {"paragraph_id": "p1", "text": "Personal devices are allowed in the workplace."},
            {"paragraph_id": "p2", "text": "Personal devices are forbidden in secured areas."},
        ]
        contradictions = detect_contradictions(evidence)
        assert len(contradictions) >= 1

    def test_numeric_mismatch(self):
        """Different numbers for the same constraint should trigger contradiction."""
        evidence = [
            {"paragraph_id": "p1", "text": "Passwords require a minimum 8 characters."},
            {"paragraph_id": "p2", "text": "Passwords require a minimum 12 characters."},
        ]
        contradictions = detect_contradictions(evidence)
        assert len(contradictions) >= 1
        assert "minimum" in contradictions[0]["rationale"].lower()

    def test_no_contradiction(self):
        """Non-conflicting evidence should produce no contradictions."""
        evidence = [
            {"paragraph_id": "p1", "text": "Data must be encrypted at rest."},
            {"paragraph_id": "p2", "text": "All backups should be stored securely."},
        ]
        contradictions = detect_contradictions(evidence)
        assert len(contradictions) == 0

    def test_empty_evidence(self):
        """Empty evidence should produce no contradictions."""
        assert detect_contradictions([]) == []

    def test_contradiction_has_confidence(self):
        """Each contradiction should have a confidence level."""
        evidence = [
            {"paragraph_id": "p1", "text": "Access is allowed for all staff."},
            {"paragraph_id": "p2", "text": "Access is not allowed after hours."},
        ]
        contradictions = detect_contradictions(evidence)
        if contradictions:
            assert contradictions[0]["confidence"] in ("low", "med", "high")


class TestContradictionPolicy:
    def test_surface_policy_adds_note(self):
        """Surface policy should add conflict note to answer."""
        contradictions = [{
            "type": "contradiction",
            "paragraph_ids": ["p1", "p2"],
            "rationale": "'must' vs 'must not'",
            "confidence": "med",
        }]
        answer, citations, notes = apply_contradiction_policy(
            "Some answer", ["p1"], contradictions, policy="surface"
        )
        assert "CONTRADICTION_SURFACED" in notes
        assert "conflict" in answer.lower()
        assert "p2" in citations  # conflicting paragraph added

    def test_abstain_on_high_policy(self):
        """abstain_on_high policy should abstain on high-confidence contradiction."""
        contradictions = [{
            "type": "contradiction",
            "paragraph_ids": ["p1", "p2"],
            "rationale": "'must' vs 'must not'; 'required' vs 'not required'",
            "confidence": "high",
        }]
        answer, citations, notes = apply_contradiction_policy(
            "Some answer", ["p1"], contradictions, policy="abstain_on_high"
        )
        assert answer == "INSUFFICIENT_EVIDENCE"
        assert "ABSTAINED_CONTRADICTION_HIGH" in notes

    def test_no_contradictions_passthrough(self):
        """No contradictions = no changes."""
        answer, citations, notes = apply_contradiction_policy(
            "Some answer", ["p1"], [], policy="surface"
        )
        assert answer == "Some answer"
        assert notes == []
