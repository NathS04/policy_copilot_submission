"""
Tests for the RAG response schema and citation validation logic.
"""
import pytest
from policy_copilot.generate.schema import RAGResponse, make_insufficient, make_llm_disabled
from policy_copilot.generate.answerer import _validate_citations, _parse_json_response


class TestRAGResponseSchema:
    def test_valid_response(self):
        resp = RAGResponse(answer="Test answer", citations=["p1", "p2"])
        assert resp.answer == "Test answer"
        assert len(resp.citations) == 2

    def test_insufficient_evidence_helper(self):
        resp = make_insufficient()
        assert resp.answer == "INSUFFICIENT_EVIDENCE"
        assert resp.citations == []

    def test_llm_disabled_helper(self):
        resp = make_llm_disabled()
        assert resp.answer == "LLM_DISABLED"
        assert resp.citations == []

    def test_missing_answer_field_raises(self):
        with pytest.raises(Exception):
            RAGResponse(citations=["p1"])


class TestCitationValidation:
    def test_invalid_citations_removed(self):
        resp = RAGResponse(answer="Some answer", citations=["valid_id", "fake_id"])
        valid = {"valid_id"}
        cleaned = _validate_citations(resp, valid)
        assert cleaned.citations == ["valid_id"]
        assert "INVALID_CITATIONS_REMOVED" in (cleaned.notes or "")

    def test_no_citations_warning(self):
        resp = RAGResponse(answer="Some answer", citations=[])
        cleaned = _validate_citations(resp, {"p1"})
        assert "NO_CITATIONS_GIVEN" in (cleaned.notes or "")

    def test_insufficient_clears_citations(self):
        resp = RAGResponse(answer="INSUFFICIENT_EVIDENCE", citations=["leftover"])
        cleaned = _validate_citations(resp, {"leftover"})
        assert cleaned.citations == []


class TestJSONParsing:
    def test_valid_json(self):
        raw = '{"answer": "Yes", "citations": ["p1"]}'
        result = _parse_json_response(raw)
        assert result is not None
        assert result["answer"] == "Yes"

    def test_json_with_markdown_fences(self):
        raw = '```json\n{"answer": "Yes", "citations": []}\n```'
        result = _parse_json_response(raw)
        assert result is not None
        assert result["answer"] == "Yes"

    def test_invalid_json(self):
        raw = "This is not JSON at all"
        result = _parse_json_response(raw)
        assert result is None
