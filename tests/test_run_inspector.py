"""
Tests for the RunInspector service.

Creates temporary run directories with known fixtures to test
listing, loading, and comparison.
"""
import json
import pytest

from policy_copilot.service.run_inspector import RunInspector
from policy_copilot.service.schemas import RunDetail, ComparisonResult


# ------------------------------------------------------------------ #
#  Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def runs_dir(tmp_path):
    """Create a temporary runs directory with two test runs."""
    # Run A: b2 baseline
    run_a = tmp_path / "b2_test_run"
    run_a.mkdir()

    (run_a / "run_config.json").write_text(json.dumps({
        "baseline": "b2",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "backend_requested": "bm25",
        "backend_used": "bm25",
    }))
    (run_a / "summary.json").write_text(json.dumps({
        "baseline": "b2",
        "total_queries": 10,
        "answer_rate": 0.90,
        "abstention_accuracy": 0.80,
        "evidence_recall_at_5": 0.75,
        "citation_precision": 0.60,
    }))

    records_a = [
        {"query_id": "q1", "question": "Test Q1?", "category": "answerable",
         "answer": "Answer 1", "is_abstained": False, "citations": ["p1"],
         "confidence": {}, "contradictions": [], "notes": [],
         "provider": "openai", "model": "gpt-4o-mini",
         "backend_requested": "bm25", "backend_used": "bm25"},
        {"query_id": "q2", "question": "Test Q2?", "category": "unanswerable",
         "answer": "INSUFFICIENT_EVIDENCE", "is_abstained": True, "citations": [],
         "confidence": {}, "contradictions": [], "notes": ["ABSTAINED"],
         "provider": "openai", "model": "gpt-4o-mini",
         "backend_requested": "bm25", "backend_used": "bm25"},
    ]
    with open(run_a / "outputs.jsonl", "w") as f:
        for r in records_a:
            f.write(json.dumps(r) + "\n")

    # Run B: b3 baseline
    run_b = tmp_path / "b3_test_run"
    run_b.mkdir()

    (run_b / "run_config.json").write_text(json.dumps({
        "baseline": "b3",
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "backend_requested": "dense",
        "backend_used": "dense",
    }))
    (run_b / "summary.json").write_text(json.dumps({
        "baseline": "b3",
        "total_queries": 10,
        "answer_rate": 0.85,
        "abstention_accuracy": 0.90,
        "evidence_recall_at_5": 0.80,
        "citation_precision": 0.75,
    }))

    records_b = [
        {"query_id": "q1", "question": "Test Q1?", "category": "answerable",
         "answer": "Better answer 1", "is_abstained": False, "citations": ["p1", "p2"],
         "confidence": {"max_rerank": 0.85}, "contradictions": [], "notes": [],
         "provider": "openai", "model": "gpt-4o-mini",
         "backend_requested": "dense", "backend_used": "dense"},
        {"query_id": "q2", "question": "Test Q2?", "category": "unanswerable",
         "answer": "INSUFFICIENT_EVIDENCE", "is_abstained": True, "citations": [],
         "confidence": {"max_rerank": 0.10}, "contradictions": [], "notes": ["ABSTAINED"],
         "provider": "openai", "model": "gpt-4o-mini",
         "backend_requested": "dense", "backend_used": "dense"},
    ]
    with open(run_b / "outputs.jsonl", "w") as f:
        for r in records_b:
            f.write(json.dumps(r) + "\n")

    return tmp_path


# ------------------------------------------------------------------ #
#  Tests: list_runs                                                    #
# ------------------------------------------------------------------ #

class TestRunInspectorListRuns:

    def test_lists_available_runs(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        runs = inspector.list_runs()

        assert len(runs) == 2
        names = {r.run_name for r in runs}
        assert "b2_test_run" in names
        assert "b3_test_run" in names

    def test_returns_empty_for_missing_dir(self, tmp_path):
        inspector = RunInspector(runs_dir=tmp_path / "nonexistent")
        runs = inspector.list_runs()
        assert runs == []

    def test_summary_fields_populated(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        runs = inspector.list_runs()

        b3 = next(r for r in runs if r.run_name == "b3_test_run")
        assert b3.baseline == "b3"
        assert b3.total_queries == 10
        assert b3.answer_rate == 0.85
        assert b3.abstention_accuracy == 0.90


# ------------------------------------------------------------------ #
#  Tests: load_run                                                     #
# ------------------------------------------------------------------ #

class TestRunInspectorLoadRun:

    def test_loads_run_detail(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        detail = inspector.load_run("b3_test_run")

        assert detail is not None
        assert isinstance(detail, RunDetail)
        assert detail.summary.baseline == "b3"
        assert len(detail.records) == 2

    def test_records_have_correct_fields(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        detail = inspector.load_run("b3_test_run")

        q1 = next(r for r in detail.records if r.query_id == "q1")
        assert q1.question == "Test Q1?"
        assert q1.answer == "Better answer 1"
        assert q1.is_abstained is False
        assert "p1" in q1.citations

    def test_returns_none_for_missing_run(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        detail = inspector.load_run("nonexistent_run")
        assert detail is None

    def test_config_loaded(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        detail = inspector.load_run("b3_test_run")

        assert detail.config.get("baseline") == "b3"
        assert detail.config.get("provider") == "openai"


# ------------------------------------------------------------------ #
#  Tests: compare_runs                                                 #
# ------------------------------------------------------------------ #

class TestRunInspectorCompare:

    def test_compare_produces_deltas(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        result = inspector.compare_runs("b2_test_run", "b3_test_run")

        assert result is not None
        assert isinstance(result, ComparisonResult)
        assert result.run_a.run_name == "b2_test_run"
        assert result.run_b.run_name == "b3_test_run"

        # B3 has better abstention (0.90 vs 0.80 = +0.10)
        assert result.metric_deltas["abstention_accuracy"] == pytest.approx(0.10, abs=0.001)
        # B3 has better citation precision (0.75 vs 0.60 = +0.15)
        assert result.metric_deltas["citation_precision"] == pytest.approx(0.15, abs=0.001)

    def test_compare_includes_per_query(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        result = inspector.compare_runs("b2_test_run", "b3_test_run")

        assert len(result.per_query) == 2
        q1 = next(pq for pq in result.per_query if pq["query_id"] == "q1")
        assert q1["answer_a"] == "Answer 1"
        assert q1["answer_b"] == "Better answer 1"

    def test_compare_returns_none_for_missing_run(self, runs_dir):
        inspector = RunInspector(runs_dir=runs_dir)
        result = inspector.compare_runs("b2_test_run", "nonexistent")
        assert result is None
