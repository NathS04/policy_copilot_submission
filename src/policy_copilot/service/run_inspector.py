"""
Run inspector — browse, load, and compare evaluation run artifacts.

Reads from the ``results/runs/`` directory produced by ``scripts/run_eval.py``.
Each run folder contains ``outputs.jsonl``, ``summary.json``, ``run_config.json``,
and optionally ``tables/metrics.csv``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from policy_copilot.logging_utils import setup_logging
from policy_copilot.service.schemas import (
    ComparisonResult,
    RunDetail,
    RunQueryRecord,
    RunSummary,
)

logger = setup_logging()

_DEFAULT_RUNS_DIR = Path("results/runs")


class RunInspector:
    """Provides read-only access to evaluation run artifacts."""

    def __init__(self, runs_dir: Optional[Path] = None):
        self.runs_dir = runs_dir or _DEFAULT_RUNS_DIR

    # ------------------------------------------------------------------ #
    #  Listing                                                             #
    # ------------------------------------------------------------------ #

    def list_runs(self) -> List[RunSummary]:
        """Return lightweight summaries for every run in the results directory."""
        if not self.runs_dir.exists():
            return []

        summaries: list[RunSummary] = []
        for run_path in sorted(self.runs_dir.iterdir()):
            if not run_path.is_dir():
                continue
            summary = self._load_summary(run_path)
            if summary is not None:
                summaries.append(summary)

        return summaries

    # ------------------------------------------------------------------ #
    #  Loading a single run                                                #
    # ------------------------------------------------------------------ #

    def load_run(self, run_name: str) -> Optional[RunDetail]:
        """Load full detail for a single run."""
        run_path = self.runs_dir / run_name
        if not run_path.is_dir():
            logger.warning("Run directory not found: %s", run_path)
            return None

        summary = self._load_summary(run_path) or RunSummary(run_name=run_name)
        config = self._read_json(run_path / "run_config.json") or {}
        records = self._load_records(run_path / "outputs.jsonl")
        metrics = self._read_json(run_path / "summary.json") or {}

        return RunDetail(
            summary=summary,
            config=config,
            records=records,
            metrics=metrics,
        )

    # ------------------------------------------------------------------ #
    #  Comparison                                                          #
    # ------------------------------------------------------------------ #

    def compare_runs(self, run_a_name: str, run_b_name: str) -> Optional[ComparisonResult]:
        """Compare two runs by their summary metrics."""
        run_a = self.load_run(run_a_name)
        run_b = self.load_run(run_b_name)
        if run_a is None or run_b is None:
            return None

        metric_keys = [
            "answer_rate", "abstention_accuracy", "evidence_recall_at_5",
            "citation_precision", "citation_recall", "ungrounded_rate",
            "support_rate_mean", "contradiction_recall", "contradiction_precision",
        ]

        deltas: Dict[str, Optional[float]] = {}
        for key in metric_keys:
            val_a = run_a.metrics.get(key)
            val_b = run_b.metrics.get(key)
            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                deltas[key] = round(val_b - val_a, 4)
            else:
                deltas[key] = None

        # Per-query pairing by query_id
        records_a = {r.query_id: r for r in run_a.records}
        records_b = {r.query_id: r for r in run_b.records}
        all_ids = sorted(set(records_a.keys()) | set(records_b.keys()))

        per_query: List[Dict[str, Any]] = []
        for qid in all_ids:
            entry: Dict[str, Any] = {"query_id": qid}
            ra = records_a.get(qid)
            rb = records_b.get(qid)
            if ra:
                entry["answer_a"] = ra.answer
                entry["abstained_a"] = ra.is_abstained
                entry["citations_a"] = ra.citations
            if rb:
                entry["answer_b"] = rb.answer
                entry["abstained_b"] = rb.is_abstained
                entry["citations_b"] = rb.citations
            per_query.append(entry)

        return ComparisonResult(
            run_a=run_a.summary,
            run_b=run_b.summary,
            metric_deltas=deltas,
            per_query=per_query,
        )

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _load_summary(self, run_path: Path) -> Optional[RunSummary]:
        summary_data = self._read_json(run_path / "summary.json")
        config_data = self._read_json(run_path / "run_config.json") or {}

        if summary_data is None and not config_data:
            return None

        summary_data = summary_data or {}

        return RunSummary(
            run_name=run_path.name,
            baseline=summary_data.get("baseline", config_data.get("baseline", "")),
            total_queries=summary_data.get("total_queries", 0),
            answer_rate=summary_data.get("answer_rate"),
            abstention_accuracy=summary_data.get("abstention_accuracy"),
            evidence_recall_at_5=summary_data.get("evidence_recall_at_5"),
            citation_precision=summary_data.get("citation_precision"),
            ungrounded_rate=summary_data.get("ungrounded_rate"),
            provider=config_data.get("provider", ""),
            model=config_data.get("model", config_data.get("model_name", "")),
            backend_requested=config_data.get("backend_requested", ""),
            backend_used=config_data.get("backend_used", ""),
            created_at=config_data.get("created_at", ""),
        )

    @staticmethod
    def _load_records(outputs_path: Path) -> List[RunQueryRecord]:
        if not outputs_path.exists():
            return []
        records: list[RunQueryRecord] = []
        with open(outputs_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    records.append(RunQueryRecord(
                        query_id=obj.get("query_id", ""),
                        question=obj.get("question", ""),
                        category=obj.get("category", ""),
                        answer=obj.get("answer", ""),
                        is_abstained=obj.get("is_abstained", False),
                        citations=obj.get("citations", []),
                        confidence=obj.get("confidence", {}),
                        contradictions=obj.get("contradictions", []),
                        notes=obj.get("notes", []),
                        latency_ms=obj.get("latency_ms"),
                        provider=obj.get("provider", ""),
                        model=obj.get("model", ""),
                        backend_requested=obj.get("backend_requested", ""),
                        backend_used=obj.get("backend_used", ""),
                    ))
                except (json.JSONDecodeError, Exception) as exc:
                    logger.debug("Skipping malformed record: %s", exc)
        return records

    @staticmethod
    def _read_json(path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as exc:
            logger.debug("Failed to read %s: %s", path, exc)
            return None
