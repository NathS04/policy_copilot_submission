"""
Tests for per-claim citation verification.
"""
from policy_copilot.verify.claim_split import split_claims, extract_all_citations
from policy_copilot.verify.citation_check import (
    verify_claim_heuristic, verify_claims, enforce_support_policy
)


class TestClaimSplitting:
    def test_split_simple_sentences(self):
        """Should split answer into sentence-level claims."""
        answer = "Policy requires 12 characters. [CITATION: p1] Passwords must be unique. [CITATION: p2]"
        claims = split_claims(answer)
        assert len(claims) == 2
        assert claims[0]["claim_id"] == "c0000"
        assert claims[1]["claim_id"] == "c0001"

    def test_extract_citations_from_claim(self):
        """Each claim should have its own citations parsed."""
        answer = "Data must be encrypted. [CITATION: doc1::p001::i000::abc123]"
        claims = split_claims(answer)
        assert len(claims) == 1
        assert "doc1::p001::i000::abc123" in claims[0]["citations"]

    def test_multiple_citations_per_claim(self):
        """A claim can cite multiple paragraphs."""
        answer = "Access is restricted. [CITATION: p1] [CITATION: p2]"
        claims = split_claims(answer)
        assert len(claims[0]["citations"]) == 2

    def test_insufficient_evidence_returns_empty(self):
        """INSUFFICIENT_EVIDENCE should produce no claims."""
        claims = split_claims("INSUFFICIENT_EVIDENCE")
        assert claims == []

    def test_extract_all_citations(self):
        """Should extract all unique citations from full answer."""
        answer = "Claim one. [CITATION: p1] Claim two. [CITATION: p2] [CITATION: p1]"
        cites = extract_all_citations(answer)
        assert cites == ["p1", "p2"]  # deduplicated, order preserved


class TestClaimVerification:
    def test_supported_claim_with_overlap(self):
        """Claim with matching keywords in evidence should be supported."""
        result = verify_claim_heuristic(
            "Passwords must be at least 12 characters",
            ["All passwords must be at least 12 characters long for security"]
        )
        assert result["supported"] is True
        assert result["jaccard"] > 0.10

    def test_unsupported_claim_no_overlap(self):
        """Claim with no matching keywords should be unsupported."""
        result = verify_claim_heuristic(
            "Dogs are friendly animals",
            ["The policy outlines encryption requirements for data at rest"]
        )
        assert result["supported"] is False

    def test_numeric_match_counts(self):
        """Shared numbers should contribute to support."""
        result = verify_claim_heuristic(
            "The minimum length is 12",
            ["Passwords require a minimum length of 12 characters"]
        )
        assert result["supported"] is True

    def test_no_cited_paragraphs(self):
        """Claim with no cited paragraph texts should be unsupported."""
        result = verify_claim_heuristic("Some claim", [])
        assert result["supported"] is False

    def test_invalid_citations_removed(self):
        """Invalid paragraph_id citations should be removed during filtering."""
        claims = [
            {"claim_id": "c0000", "text": "Data must be encrypted",
             "citations": ["valid_p1", "invalid_p99"]}
        ]
        evidence_lookup = {"valid_p1": "Data storage requires encryption at rest"}
        result = verify_claims(claims, evidence_lookup)
        # only valid_p1 should appear in citations; invalid_p99 is not in evidence
        assert result["claims"][0]["citations"] == ["valid_p1"]


class TestSupportPolicyEnforcement:
    def test_low_support_rate_triggers_abstention(self):
        """If support rate < min, should abstain."""
        verification = {
            "claims": [
                {"claim_id": "c0000", "text": "claim 1", "citations": [],
                 "supported": False},
                {"claim_id": "c0001", "text": "claim 2", "citations": [],
                 "supported": False},
            ],
            "supported_claims": 0,
            "unsupported_claims": 2,
            "support_rate": 0.0,
        }
        answer, citations, notes = enforce_support_policy(
            "Some answer", ["p1"], verification, min_support_rate=0.80
        )
        assert answer == "INSUFFICIENT_EVIDENCE"
        assert citations == []
        assert any("ABSTAINED_LOW_SUPPORT_RATE" in n for n in notes)

    def test_unsupported_claims_removed_above_threshold(self):
        """If support rate >= min but some claims unsupported, they are removed."""
        verification = {
            "claims": [
                {"claim_id": "c0000", "text": "Supported claim",
                 "citations": ["p1"], "supported": True},
                {"claim_id": "c0001", "text": "Unsupported claim",
                 "citations": [], "supported": False},
                {"claim_id": "c0002", "text": "Another supported claim",
                 "citations": ["p2"], "supported": True},
                {"claim_id": "c0003", "text": "Yet another supported",
                 "citations": ["p1"], "supported": True},
                {"claim_id": "c0004", "text": "One more supported",
                 "citations": ["p2"], "supported": True},
            ],
            "supported_claims": 4,
            "unsupported_claims": 1,
            "support_rate": 0.80,
        }
        answer, citations, notes = enforce_support_policy(
            "Some answer", ["p1", "p2"], verification, min_support_rate=0.80
        )
        assert "UNSUPPORTED_CLAIMS_REMOVED" in notes
        assert "Unsupported claim" not in answer

    def test_insufficient_evidence_passthrough(self):
        """INSUFFICIENT_EVIDENCE should pass through unchanged."""
        answer, citations, notes = enforce_support_policy(
            "INSUFFICIENT_EVIDENCE", [], {"support_rate": 0.0}, 0.80
        )
        assert answer == "INSUFFICIENT_EVIDENCE"
        assert citations == []
