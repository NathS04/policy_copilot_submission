"""
Reviewer service — supports human rubric scoring of query results.

Loads saved query results from evaluation runs, presents them for
human review, captures rubric scores, and exports structured JSON/CSV.
"""
from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReviewRubric(BaseModel):
    """A single human review of a query result."""

    review_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    query_id: str = ""
    question: str = ""
    rater_id: str = "rater_1"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    groundedness: Optional[int] = Field(
        None, ge=1, le=5, description="1-5: Is the answer supported by cited evidence?"
    )
    usefulness: Optional[int] = Field(
        None, ge=1, le=5, description="1-5: Does the answer address the question?"
    )
    citation_correctness: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="1-5: Are the citations accurate and relevant?",
    )
    notes: str = ""


class ReviewSession(BaseModel):
    """A collection of reviews from a single scoring session."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    run_name: str = ""
    reviews: List[ReviewRubric] = Field(default_factory=list)


class ReviewerService:
    """Load query results for review, capture scores, and export."""

    def __init__(self, runs_dir: Optional[Path] = None):
        if runs_dir is None:
            runs_dir = Path("results/runs")
        self._runs_dir = runs_dir

    def load_queries_from_run(self, run_name: str) -> List[Dict[str, Any]]:
        """Load per-query records from a run's outputs.jsonl."""
        outputs_path = self._runs_dir / run_name / "outputs.jsonl"
        if not outputs_path.exists():
            return []
        records = []
        with open(outputs_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    @staticmethod
    def create_session(run_name: str) -> ReviewSession:
        return ReviewSession(run_name=run_name)

    @staticmethod
    def add_review(session: ReviewSession, review: ReviewRubric) -> None:
        session.reviews.append(review)

    @staticmethod
    def export_json(session: ReviewSession) -> str:
        return session.model_dump_json(indent=2)

    @staticmethod
    def export_csv(session: ReviewSession) -> str:
        """Export reviews as CSV string."""
        if not session.reviews:
            return ""
        fields = [
            "review_id",
            "query_id",
            "question",
            "rater_id",
            "timestamp",
            "groundedness",
            "usefulness",
            "citation_correctness",
            "notes",
        ]
        import io

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fields)
        writer.writeheader()
        for r in session.reviews:
            writer.writerow(
                {k: getattr(r, k, "") for k in fields}
            )
        return buf.getvalue()

    @staticmethod
    def summary_stats(session: ReviewSession) -> Dict[str, Any]:
        """Compute mean scores across all completed reviews."""
        if not session.reviews:
            return {}
        dims = ["groundedness", "usefulness", "citation_correctness"]
        stats: Dict[str, Any] = {"total_reviews": len(session.reviews)}
        for dim in dims:
            vals = [
                getattr(r, dim)
                for r in session.reviews
                if getattr(r, dim) is not None
            ]
            stats[f"{dim}_mean"] = round(sum(vals) / len(vals), 2) if vals else None
            stats[f"{dim}_count"] = len(vals)
        return stats
