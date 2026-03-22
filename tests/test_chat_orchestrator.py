"""
Tests for the ChatOrchestrator service layer.

Uses mock retrievers and mocked answerer to test pipeline flow without
requiring ML models, API keys, or a FAISS index.
"""
from unittest.mock import MagicMock, patch

from policy_copilot.service.chat_orchestrator import ChatOrchestrator
from policy_copilot.service.schemas import QueryResult


# ------------------------------------------------------------------ #
#  Fixtures                                                            #
# ------------------------------------------------------------------ #

def _make_evidence(n=3, high_score=True):
    """Build a list of mock evidence dicts."""
    base_score = 0.85 if high_score else 0.10
    return [
        {
            "paragraph_id": f"doc1::p1::i{i}::abc{i}",
            "doc_id": "doc1",
            "page": 1,
            "text": f"Policy paragraph {i} about academic integrity requirements.",
            "source_file": "handbook.pdf",
            "score": base_score - i * 0.05,
            "score_retrieve": base_score - i * 0.05,
            "score_rerank": base_score - i * 0.02,
            "backend": "dense",
        }
        for i in range(n)
    ]


def _mock_retriever(evidence=None, loaded=True):
    retriever = MagicMock()
    retriever.loaded = loaded
    retriever.backend_used = "dense"
    retriever.backend = "dense"
    retriever.fusion_method = ""
    retriever.retrieve.return_value = evidence or _make_evidence()
    return retriever


def _mock_rag_response(answer="Academic integrity requires honest work.",
                       citations=None):
    from policy_copilot.generate.schema import RAGResponse
    return RAGResponse(
        answer=answer,
        citations=citations or ["doc1::p1::i0::abc0"],
        notes=None,
    )


# ------------------------------------------------------------------ #
#  Tests: normal flow                                                  #
# ------------------------------------------------------------------ #

class TestChatOrchestratorNormalFlow:

    @patch("policy_copilot.generate.answerer.Answerer")
    def test_returns_query_result(self, mock_answerer_cls):
        """process_query returns a valid QueryResult."""
        evidence = _make_evidence()
        retriever = _mock_retriever(evidence)

        mock_answerer = MagicMock()
        resp = _mock_rag_response()
        mock_answerer.generate_b3.return_value = (resp, {"latency_ms": 100, "provider": "openai", "model": "gpt-4o-mini"})
        mock_answerer_cls.return_value = mock_answerer

        orch = ChatOrchestrator(retriever=retriever)
        result = orch.process_query("What is academic integrity?")

        assert isinstance(result, QueryResult)
        assert result.question == "What is academic integrity?"
        assert result.answer != ""
        assert result.query_id != ""
        assert result.timestamp != ""

    @patch("policy_copilot.generate.answerer.Answerer")
    def test_populates_evidence(self, mock_answerer_cls):
        """Evidence items are populated with scores."""
        evidence = _make_evidence()
        retriever = _mock_retriever(evidence)

        mock_answerer = MagicMock()
        resp = _mock_rag_response()
        mock_answerer.generate_b3.return_value = (resp, {"latency_ms": 50})
        mock_answerer_cls.return_value = mock_answerer

        orch = ChatOrchestrator(retriever=retriever)
        result = orch.process_query("Test")

        assert len(result.evidence) > 0
        for ev in result.evidence:
            assert ev.paragraph_id != ""
            assert ev.score_retrieve >= 0


# ------------------------------------------------------------------ #
#  Tests: abstention path                                              #
# ------------------------------------------------------------------ #

class TestChatOrchestratorAbstention:

    def test_abstains_on_low_confidence(self):
        """When evidence scores are below threshold, the system abstains."""
        evidence = _make_evidence(high_score=False)
        retriever = _mock_retriever(evidence)

        orch = ChatOrchestrator(retriever=retriever)
        result = orch.process_query("Some unanswerable question?")

        assert result.is_abstained is True
        assert result.answer == "INSUFFICIENT_EVIDENCE"
        assert "ABSTAINED_LOW_CONFIDENCE" in result.notes

    def test_abstention_records_confidence(self):
        """Abstention result includes confidence metrics."""
        evidence = _make_evidence(high_score=False)
        retriever = _mock_retriever(evidence)

        orch = ChatOrchestrator(retriever=retriever)
        result = orch.process_query("Unanswerable?")

        assert result.confidence_max_rerank >= 0
        assert result.abstain_threshold > 0


# ------------------------------------------------------------------ #
#  Tests: retriever not loaded                                         #
# ------------------------------------------------------------------ #

class TestChatOrchestratorNoRetriever:

    def test_empty_evidence_when_retriever_not_loaded(self):
        """When retriever is not loaded, evidence is empty and system abstains."""
        retriever = _mock_retriever(loaded=False)

        orch = ChatOrchestrator(retriever=retriever)
        result = orch.process_query("Test query")

        assert result.is_abstained is True
        assert len(result.evidence) == 0


# ------------------------------------------------------------------ #
#  Tests: config overrides                                             #
# ------------------------------------------------------------------ #

class TestChatOrchestratorConfig:

    def test_config_overrides_applied(self):
        """Config overrides modify effective config."""
        retriever = _mock_retriever(_make_evidence(high_score=False))

        orch = ChatOrchestrator(
            retriever=retriever,
            config_overrides={"abstain_threshold": 0.01},
        )
        cfg = orch._effective_config()
        assert cfg["abstain_threshold"] == 0.01


# ------------------------------------------------------------------ #
#  Tests: latency tracking                                             #
# ------------------------------------------------------------------ #

class TestChatOrchestratorLatency:

    def test_latency_recorded(self):
        """Latency breakdown is populated."""
        evidence = _make_evidence(high_score=False)
        retriever = _mock_retriever(evidence)

        orch = ChatOrchestrator(retriever=retriever)
        result = orch.process_query("Test")

        assert result.latency.retrieval_ms >= 0
        assert result.latency.rerank_ms >= 0
