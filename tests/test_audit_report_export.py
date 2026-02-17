"""
Tests for audit report export — JSON, HTML, and Markdown.

Verifies that all required fields are present in exported reports
and that round-trip serialisation works correctly.
"""
import json
import pytest

from policy_copilot.service.schemas import (
    AuditReport,
    ClaimDetail,
    ClaimVerificationResult,
    ContradictionAlert,
    CriticFinding,
    EvidenceItem,
    LatencyBreakdown,
    QueryResult,
)
from policy_copilot.service.audit_report_service import AuditReportService


# ------------------------------------------------------------------ #
#  Fixtures                                                            #
# ------------------------------------------------------------------ #

def _make_query_result() -> QueryResult:
    """Build a representative QueryResult for testing."""
    return QueryResult(
        question="What is the policy on extensions?",
        answer="Extensions must be requested before the deadline. [CITATION: doc1::p1::i0::abc0]",
        citations=["doc1::p1::i0::abc0"],
        evidence=[
            EvidenceItem(
                paragraph_id="doc1::p1::i0::abc0",
                doc_id="doc1",
                page=3,
                text="Students must submit extension requests prior to the original deadline.",
                source_file="handbook.pdf",
                score_retrieve=0.85,
                score_rerank=0.92,
            ),
        ],
        confidence_max_rerank=0.92,
        confidence_mean_top3=0.88,
        abstain_threshold=0.30,
        claim_verification=ClaimVerificationResult(
            claims=[
                ClaimDetail(
                    claim_id=1,
                    text="Extensions must be requested before the deadline.",
                    citations=["doc1::p1::i0::abc0"],
                    supported=True,
                    support_rationale="Jaccard=0.35",
                    evidence_excerpt="Students must submit extension requests...",
                ),
            ],
            supported_claims=1,
            unsupported_claims=0,
            support_rate=1.0,
        ),
        contradictions=[
            ContradictionAlert(
                paragraph_ids=["doc1::p1::i0::abc0", "doc1::p2::i0::def0"],
                rationale="'required' vs 'not required'",
                confidence="med",
                tier=1,
                text_a="Extensions are required before deadline.",
                text_b="Extensions are not required for minor coursework.",
            ),
        ],
        critic_findings=[
            CriticFinding(
                label="L1",
                label_name="Normative Language",
                paragraph_id="doc1::p1::i0::abc0",
                triggers=["obviously"],
                rationale="obviously",
                text_excerpt="Obviously students must...",
            ),
        ],
        latency=LatencyBreakdown(
            retrieval_ms=15.0,
            rerank_ms=120.0,
            llm_gen_ms=800.0,
            verify_ms=5.0,
            contradictions_ms=3.0,
            critic_ms=2.0,
            total_ms=945.0,
        ),
        provider="openai",
        model="gpt-4o-mini",
        backend_requested="dense",
        backend_used="dense",
        config_snapshot={"provider": "openai", "model": "gpt-4o-mini"},
    )


# ------------------------------------------------------------------ #
#  Tests: JSON export                                                  #
# ------------------------------------------------------------------ #

class TestAuditReportJSON:

    def test_json_contains_required_fields(self):
        """JSON export includes all required audit fields."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        json_str = AuditReportService.to_json(report)
        data = json.loads(json_str)

        assert "report_id" in data
        assert "generated_at" in data
        assert "query_result" in data

        qr_data = data["query_result"]
        assert qr_data["question"] == "What is the policy on extensions?"
        assert "answer" in qr_data
        assert "citations" in qr_data
        assert "evidence" in qr_data
        assert "claim_verification" in qr_data
        assert "contradictions" in qr_data
        assert "critic_findings" in qr_data
        assert "latency" in qr_data
        assert "config_snapshot" in qr_data
        assert "provider" in qr_data
        assert "backend_requested" in qr_data

    def test_json_round_trip(self):
        """JSON can be parsed back into an AuditReport."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        json_str = AuditReportService.to_json(report)

        restored = AuditReport.model_validate_json(json_str)
        assert restored.report_id == report.report_id
        assert restored.query_result.question == qr.question
        assert len(restored.query_result.evidence) == 1

    def test_json_contains_evidence_scores(self):
        """Evidence items in JSON have both retrieve and rerank scores."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        data = json.loads(AuditReportService.to_json(report))

        ev = data["query_result"]["evidence"][0]
        assert "score_retrieve" in ev
        assert "score_rerank" in ev
        assert ev["score_retrieve"] == 0.85


# ------------------------------------------------------------------ #
#  Tests: HTML export                                                  #
# ------------------------------------------------------------------ #

class TestAuditReportHTML:

    def test_html_contains_question(self):
        """HTML export includes the question."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        html = AuditReportService.to_html(report)

        assert "What is the policy on extensions?" in html

    def test_html_contains_claim_verification(self):
        """HTML export includes claim verification section."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        html = AuditReportService.to_html(report)

        assert "Claim 1" in html
        assert "Supported" in html

    def test_html_contains_contradiction(self):
        """HTML export includes contradiction section."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        html = AuditReportService.to_html(report)

        assert "Contradiction" in html

    def test_html_contains_metadata(self):
        """HTML export includes provider and model metadata."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        html = AuditReportService.to_html(report)

        assert "openai" in html
        assert "gpt-4o-mini" in html


# ------------------------------------------------------------------ #
#  Tests: Markdown export                                              #
# ------------------------------------------------------------------ #

class TestAuditReportMarkdown:

    def test_markdown_contains_question(self):
        """Markdown export includes the question."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        md = AuditReportService.to_markdown(report)

        assert "What is the policy on extensions?" in md

    def test_markdown_contains_evidence(self):
        """Markdown export lists evidence items."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        md = AuditReportService.to_markdown(report)

        assert "doc1::p1::i0::abc0" in md


# ------------------------------------------------------------------ #
#  Tests: summary text                                                 #
# ------------------------------------------------------------------ #

class TestAuditReportSummary:

    def test_summary_text(self):
        """AuditReport.summary_text() provides a readable overview."""
        qr = _make_query_result()
        report = AuditReportService.generate_report(qr)
        summary = report.summary_text()

        assert "Audit Report" in summary
        assert "Extensions" in summary
        assert "Support rate: 100.00%" in summary
