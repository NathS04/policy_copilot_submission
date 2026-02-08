"""
Tests for the Reviewer Service — rubric capture, export, and summary stats.
"""
import csv
import io
import json
import tempfile
from pathlib import Path

import pytest

from policy_copilot.service.reviewer_service import (
    ReviewerService,
    ReviewRubric,
    ReviewSession,
)


class TestReviewRubric:

    def test_rubric_defaults(self):
        r = ReviewRubric()
        assert r.groundedness is None
        assert r.usefulness is None
        assert r.citation_correctness is None
        assert r.rater_id == "rater_1"

    def test_rubric_with_scores(self):
        r = ReviewRubric(
            query_id="q1",
            question="What is X?",
            groundedness=4,
            usefulness=5,
            citation_correctness=3,
        )
        assert r.groundedness == 4
        assert r.usefulness == 5
        assert r.citation_correctness == 3

    def test_rubric_validation_rejects_out_of_range(self):
        with pytest.raises(Exception):
            ReviewRubric(groundedness=0)
        with pytest.raises(Exception):
            ReviewRubric(usefulness=6)


class TestReviewSession:

    def test_create_session(self):
        session = ReviewerService.create_session("b3_final")
        assert session.run_name == "b3_final"
        assert session.reviews == []
        assert len(session.session_id) == 8

    def test_add_review(self):
        session = ReviewerService.create_session("b3_final")
        review = ReviewRubric(query_id="q1", groundedness=4, usefulness=5, citation_correctness=3)
        ReviewerService.add_review(session, review)
        assert len(session.reviews) == 1
        assert session.reviews[0].query_id == "q1"


class TestExportJSON:

    def test_json_export_round_trip(self):
        session = ReviewerService.create_session("b3_final")
        ReviewerService.add_review(session, ReviewRubric(
            query_id="q1", groundedness=4, usefulness=5, citation_correctness=3, notes="good"
        ))
        json_str = ReviewerService.export_json(session)
        data = json.loads(json_str)
        assert data["run_name"] == "b3_final"
        assert len(data["reviews"]) == 1
        assert data["reviews"][0]["groundedness"] == 4


class TestExportCSV:

    def test_csv_export_headers(self):
        session = ReviewerService.create_session("b3_final")
        ReviewerService.add_review(session, ReviewRubric(
            query_id="q1", groundedness=4, usefulness=5, citation_correctness=3
        ))
        csv_str = ReviewerService.export_csv(session)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["query_id"] == "q1"
        assert rows[0]["groundedness"] == "4"
        assert rows[0]["usefulness"] == "5"

    def test_csv_export_empty_session(self):
        session = ReviewerService.create_session("b3_final")
        assert ReviewerService.export_csv(session) == ""


class TestSummaryStats:

    def test_summary_with_reviews(self):
        session = ReviewerService.create_session("test")
        for g, u, c in [(4, 5, 3), (5, 4, 4), (3, 3, 5)]:
            ReviewerService.add_review(session, ReviewRubric(
                query_id=f"q{g}", groundedness=g, usefulness=u, citation_correctness=c
            ))
        stats = ReviewerService.summary_stats(session)
        assert stats["total_reviews"] == 3
        assert stats["groundedness_mean"] == 4.0
        assert stats["usefulness_mean"] == 4.0
        assert stats["citation_correctness_mean"] == 4.0

    def test_summary_empty(self):
        session = ReviewerService.create_session("test")
        assert ReviewerService.summary_stats(session) == {}


class TestLoadQueries:

    def test_load_from_run(self, tmp_path):
        run_dir = tmp_path / "results" / "runs" / "test_run"
        run_dir.mkdir(parents=True)
        records = [
            {"query_id": "q1", "question": "What?", "answer": "This.", "is_abstained": False},
            {"query_id": "q2", "question": "Where?", "answer": "Here.", "is_abstained": True},
        ]
        with open(run_dir / "outputs.jsonl", "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        svc = ReviewerService(runs_dir=tmp_path / "results" / "runs")
        loaded = svc.load_queries_from_run("test_run")
        assert len(loaded) == 2
        assert loaded[0]["query_id"] == "q1"

    def test_load_missing_run(self, tmp_path):
        svc = ReviewerService(runs_dir=tmp_path)
        assert svc.load_queries_from_run("nonexistent") == []
