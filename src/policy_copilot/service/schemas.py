"""
Pydantic models for the service layer.

All structured outputs used by chat orchestration, audit export,
and run inspection share these schemas to enforce consistency
across the UI, export, and test boundaries.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  Evidence                                                            #
# ------------------------------------------------------------------ #

class EvidenceItem(BaseModel):
    """A single retrieved evidence paragraph with scoring metadata."""
    paragraph_id: str = ""
    doc_id: str = ""
    page: int = 0
    text: str = ""
    source_file: str = ""
    score_retrieve: float = 0.0
    score_rerank: float = 0.0
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    fused_score: Optional[float] = None
    backend: str = ""


# ------------------------------------------------------------------ #
#  Claim verification                                                  #
# ------------------------------------------------------------------ #

class ClaimDetail(BaseModel):
    """Verification result for a single claim."""
    claim_id: Any = 0
    text: str = ""
    citations: List[str] = Field(default_factory=list)
    supported: bool = True
    support_rationale: str = ""
    verification_tier: int = 1
    jaccard: Optional[float] = None
    evidence_excerpt: str = ""


class ClaimVerificationResult(BaseModel):
    """Aggregate verification across all claims in an answer."""
    claims: List[ClaimDetail] = Field(default_factory=list)
    supported_claims: int = 0
    unsupported_claims: int = 0
    support_rate: float = 1.0


# ------------------------------------------------------------------ #
#  Contradictions                                                      #
# ------------------------------------------------------------------ #

class ContradictionAlert(BaseModel):
    """A detected contradiction between two evidence paragraphs."""
    paragraph_ids: List[str] = Field(default_factory=list)
    rationale: str = ""
    confidence: str = "low"
    tier: int = 1
    text_a: str = ""
    text_b: str = ""


# ------------------------------------------------------------------ #
#  Critic                                                              #
# ------------------------------------------------------------------ #

class CriticFinding(BaseModel):
    """A single critic flag on a piece of text."""
    label: str = ""
    label_name: str = ""
    paragraph_id: str = ""
    triggers: List[str] = Field(default_factory=list)
    rationale: str = ""
    text_excerpt: str = ""


# ------------------------------------------------------------------ #
#  Latency breakdown                                                   #
# ------------------------------------------------------------------ #

class LatencyBreakdown(BaseModel):
    """Per-stage timing in milliseconds."""
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    llm_gen_ms: float = 0.0
    verify_ms: float = 0.0
    contradictions_ms: float = 0.0
    critic_ms: float = 0.0
    total_ms: float = 0.0


# ------------------------------------------------------------------ #
#  QueryResult — the primary output of ChatOrchestrator                #
# ------------------------------------------------------------------ #

class QueryResult(BaseModel):
    """Complete result from a single chat orchestration query."""
    query_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    question: str = ""
    answer: str = ""
    is_abstained: bool = False
    abstention_reason: str = ""

    citations: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)

    confidence_max_rerank: float = 0.0
    confidence_mean_top3: float = 0.0
    abstain_threshold: float = 0.30

    claim_verification: Optional[ClaimVerificationResult] = None
    contradictions: List[ContradictionAlert] = Field(default_factory=list)
    critic_findings: List[CriticFinding] = Field(default_factory=list)

    notes: List[str] = Field(default_factory=list)
    latency: LatencyBreakdown = Field(default_factory=LatencyBreakdown)

    provider: str = ""
    model: str = ""
    backend_requested: str = ""
    backend_used: str = ""
    fusion_method: str = ""

    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ------------------------------------------------------------------ #
#  Audit Report                                                        #
# ------------------------------------------------------------------ #

class AuditReport(BaseModel):
    """Exportable audit dossier for a single query."""
    report_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    query_result: QueryResult = Field(default_factory=QueryResult)

    def summary_text(self) -> str:
        qr = self.query_result
        lines = [
            f"Audit Report: {self.report_id}",
            f"Generated: {self.generated_at}",
            f"Question: {qr.question}",
            f"Answer: {qr.answer[:200]}{'...' if len(qr.answer) > 200 else ''}",
            f"Abstained: {qr.is_abstained}",
            f"Citations: {len(qr.citations)}",
            f"Evidence items: {len(qr.evidence)}",
            f"Contradictions: {len(qr.contradictions)}",
            f"Critic flags: {len(qr.critic_findings)}",
        ]
        if qr.claim_verification:
            lines.append(
                f"Support rate: {qr.claim_verification.support_rate:.2%}"
            )
        return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Run Inspector models                                                #
# ------------------------------------------------------------------ #

class RunSummary(BaseModel):
    """Lightweight summary of a single evaluation run."""
    run_name: str = ""
    baseline: str = ""
    total_queries: int = 0
    answer_rate: Optional[float] = None
    abstention_accuracy: Optional[float] = None
    evidence_recall_at_5: Optional[float] = None
    citation_precision: Optional[float] = None
    ungrounded_rate: Optional[Any] = None
    provider: str = ""
    model: str = ""
    backend_requested: str = ""
    backend_used: str = ""
    created_at: str = ""


class RunQueryRecord(BaseModel):
    """A single query record from a run's outputs.jsonl."""
    query_id: str = ""
    question: str = ""
    category: str = ""
    answer: str = ""
    is_abstained: bool = False
    citations: List[str] = Field(default_factory=list)
    confidence: Dict[str, Any] = Field(default_factory=dict)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    latency_ms: Any = None
    provider: str = ""
    model: str = ""
    backend_requested: str = ""
    backend_used: str = ""


class RunDetail(BaseModel):
    """Full detail of an evaluation run."""
    summary: RunSummary = Field(default_factory=RunSummary)
    config: Dict[str, Any] = Field(default_factory=dict)
    records: List[RunQueryRecord] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ComparisonResult(BaseModel):
    """Side-by-side comparison of two runs."""
    run_a: RunSummary = Field(default_factory=RunSummary)
    run_b: RunSummary = Field(default_factory=RunSummary)
    metric_deltas: Dict[str, Optional[float]] = Field(default_factory=dict)
    per_query: List[Dict[str, Any]] = Field(default_factory=list)
