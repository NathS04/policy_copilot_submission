"""
Acceptance test: HTML audit export must work in the default test environment.

This test fails if jinja2 is missing from the dev dependency group, which
would mean 'pip install -e .[dev]' + 'pytest -q' produces a broken test run.
"""


def test_jinja2_importable():
    """jinja2 must be available in the test environment."""
    import jinja2
    assert jinja2 is not None


def test_html_export_produces_real_html():
    """AuditReportService.to_html() must produce a full audit report, not a fallback."""
    from policy_copilot.service.schemas import (
        ClaimDetail,
        ClaimVerificationResult,
        EvidenceItem,
        QueryResult,
    )
    from policy_copilot.service.audit_report_service import AuditReportService

    qr = QueryResult(
        question="Test question",
        answer="Test answer [CITATION: doc1::p1::i0::x]",
        citations=["doc1::p1::i0::x"],
        evidence=[EvidenceItem(paragraph_id="doc1::p1::i0::x", text="Evidence text.")],
        claim_verification=ClaimVerificationResult(
            claims=[ClaimDetail(claim_id=1, text="Test claim", supported=True)],
            supported_claims=1,
            unsupported_claims=0,
            support_rate=1.0,
        ),
    )
    report = AuditReportService.generate_report(qr)
    html = AuditReportService.to_html(report)

    assert "Jinja2 not installed" not in html, "HTML export fell back to stub — jinja2 not available"
    assert "Claim 1" in html
    assert "Test question" in html
    assert "Supported" in html
