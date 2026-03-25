"""
Chat orchestrator — the reusable B3 pipeline extracted from run_eval.py.

Runs the full evidence-grounded pipeline for a single interactive query:
    retrieve -> rerank -> abstain -> generate -> verify -> contradictions -> critic

This module has NO dependency on Streamlit or any UI framework.  It is the
single source of truth for the interactive query path, shared by the
Streamlit UI and any future API layer.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging
from policy_copilot.service.schemas import (
    ClaimDetail,
    ClaimVerificationResult,
    ContradictionAlert,
    CriticFinding,
    EvidenceItem,
    LatencyBreakdown,
    QueryResult,
)

logger = setup_logging()

# Label ID -> human-readable name mapping
_LABEL_NAMES: Dict[str, str] = {
    "L1": "Normative Language",
    "L2": "Framing Imbalance",
    "L3": "Unsupported Claim",
    "L4": "Internal Contradiction",
    "L5": "False Dilemma",
    "L6": "Slippery Slope",
}


class ChatOrchestrator:
    """Runs the full B3 pipeline for a single interactive query.

    Parameters
    ----------
    retriever
        A pre-initialised ``Retriever`` (or ``HybridRetriever``) instance.
    config_overrides
        Optional dict of config keys to override (ablation toggles, thresholds).
    """

    def __init__(
        self,
        retriever: Any = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ):
        self._retriever = retriever
        self._overrides = config_overrides or {}

    # ----- public interface ------------------------------------------------

    def process_query(self, question: str) -> QueryResult:
        """Execute the full pipeline and return a structured ``QueryResult``."""
        cfg = self._effective_config()
        notes: list[str] = []
        timings = LatencyBreakdown()

        # -- Step 1: Retrieve candidates ------------------------------------
        retrieve_k = cfg["retrieve_k_candidates"]
        t0 = time.time()
        candidates = self._retrieve(question, retrieve_k)
        timings.retrieval_ms = round((time.time() - t0) * 1000, 1)

        backend_requested = cfg.get("backend_requested", "dense")
        backend_used = getattr(self._retriever, "backend_used",
                               getattr(self._retriever, "backend", backend_requested))
        fusion_method = getattr(self._retriever, "fusion_method", "")

        # -- Step 2: Rerank -------------------------------------------------
        rerank_k = cfg["rerank_k_final"]
        t0 = time.time()
        top_evidence, rerank_notes = self._rerank(
            question, candidates, rerank_k, cfg
        )
        notes.extend(rerank_notes)
        timings.rerank_ms = round((time.time() - t0) * 1000, 1)

        # -- Step 3: Confidence / abstention --------------------------------
        from policy_copilot.verify.abstain import compute_confidence, should_abstain

        confidence = compute_confidence(top_evidence)
        threshold = cfg["abstain_threshold"]

        if should_abstain(confidence, threshold):
            return self._build_abstention_result(
                question, top_evidence, confidence, threshold,
                notes + ["ABSTAINED_LOW_CONFIDENCE"],
                timings, cfg, backend_requested, backend_used, fusion_method,
            )

        # -- Step 4: Generate answer ----------------------------------------
        t0 = time.time()
        try:
            from policy_copilot.generate.answerer import Answerer
            answerer = Answerer()
            resp, meta = answerer.generate_b3(
                question, top_evidence, allow_fallback=True
            )
        except Exception as exc:
            logger.error("Generation failed: %s", exc)
            return self._build_error_result(
                question, top_evidence, confidence, threshold,
                notes + [f"ERROR: {exc}"],
                timings, cfg, backend_requested, backend_used, fusion_method,
            )
        timings.llm_gen_ms = round(meta.get("latency_ms", 0), 1)

        from policy_copilot.service.schemas import TokenUsage
        token_usage = None
        usage = meta.get("usage")
        if isinstance(usage, dict):
            token_usage = TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )

        answer = resp.answer
        citations = list(resp.citations)
        if resp.notes:
            notes.append(resp.notes)

        # -- Step 5: Claim verification -------------------------------------
        claim_verification: Optional[ClaimVerificationResult] = None
        if answer not in ("INSUFFICIENT_EVIDENCE", "LLM_DISABLED"):
            t0 = time.time()
            claim_verification, answer, citations, verify_notes = (
                self._verify_claims(answer, citations, top_evidence, cfg)
            )
            notes.extend(verify_notes)
            timings.verify_ms = round((time.time() - t0) * 1000, 1)

        # -- Step 6: Contradiction detection --------------------------------
        contradictions: list[ContradictionAlert] = []
        if answer not in ("INSUFFICIENT_EVIDENCE", "LLM_DISABLED"):
            t0 = time.time()
            contradictions, answer, citations, contra_notes = (
                self._detect_contradictions(answer, citations, top_evidence, cfg)
            )
            notes.extend(contra_notes)
            timings.contradictions_ms = round((time.time() - t0) * 1000, 1)

        # -- Step 7: Critic -------------------------------------------------
        critic_findings: list[CriticFinding] = []
        if answer not in ("INSUFFICIENT_EVIDENCE", "LLM_DISABLED"):
            t0 = time.time()
            critic_findings = self._run_critic(top_evidence)
            timings.critic_ms = round((time.time() - t0) * 1000, 1)

        # -- Build result ---------------------------------------------------
        timings.total_ms = round(
            timings.retrieval_ms + timings.rerank_ms + timings.llm_gen_ms
            + timings.verify_ms + timings.contradictions_ms + timings.critic_ms,
            1,
        )

        evidence_items = [self._to_evidence_item(e) for e in top_evidence]

        return QueryResult(
            question=question,
            answer=answer,
            is_abstained=(answer == "INSUFFICIENT_EVIDENCE"),
            abstention_reason=(
                "Low support rate" if "ABSTAINED_LOW_SUPPORT_RATE" in " ".join(notes)
                else ""
            ),
            citations=citations,
            evidence=evidence_items,
            confidence_max_rerank=confidence.get("max_rerank", 0.0),
            confidence_mean_top3=confidence.get("mean_top3_rerank", 0.0),
            abstain_threshold=threshold,
            claim_verification=claim_verification,
            contradictions=contradictions,
            critic_findings=critic_findings,
            notes=notes,
            latency=timings,
            token_usage=token_usage,
            provider=meta.get("provider", cfg.get("provider", "")),
            model=meta.get("model", cfg.get("model", "")),
            backend_requested=backend_requested,
            backend_used=str(backend_used),
            fusion_method=fusion_method,
            config_snapshot=cfg,
        )

    # ----- private pipeline steps ------------------------------------------

    def _retrieve(self, question: str, k: int) -> list[dict]:
        if self._retriever is None or not getattr(self._retriever, "loaded", False):
            logger.warning("Retriever not loaded; returning empty evidence.")
            return []
        return self._retriever.retrieve(question, k=k)

    def _rerank(
        self, question: str, candidates: list[dict], top_k: int, cfg: dict,
    ) -> tuple[list[dict], list[str]]:
        notes: list[str] = []
        if cfg.get("no_rerank"):
            for c in candidates:
                c["score_retrieve"] = c.get("score", 0.0)
                c["score_rerank"] = c.get("score", 0.0)
            notes.append("RERANK_DISABLED")
            return candidates[:top_k], notes

        try:
            from policy_copilot.rerank.reranker import Reranker
            reranker = Reranker(
                model_name=cfg.get("rerank_model", "cross-encoder/ms-marco-MiniLM-L-6-v2")
            )
            top_evidence = reranker.rerank(question, candidates, top_k=top_k)
            if reranker.fallback:
                notes.append("RERANK_FALLBACK")
            return top_evidence, notes
        except Exception as exc:
            logger.warning("Reranker unavailable (%s); using retrieval scores.", exc)
            for c in candidates:
                c["score_retrieve"] = c.get("score", 0.0)
                c["score_rerank"] = c.get("score", 0.0)
            notes.append("RERANK_FALLBACK")
            return candidates[:top_k], notes

    def _verify_claims(
        self, answer: str, citations: list[str],
        evidence: list[dict], cfg: dict,
    ) -> tuple[Optional[ClaimVerificationResult], str, list[str], list[str]]:
        from policy_copilot.verify.claim_split import split_claims, extract_all_citations
        from policy_copilot.verify.citation_check import verify_claims, enforce_support_policy

        notes: list[str] = []
        claims = split_claims(answer)
        inline_cites = extract_all_citations(answer)
        for c in inline_cites:
            if c not in citations:
                citations.append(c)

        evidence_lookup = {
            e.get("paragraph_id", ""): e.get("text", "") for e in evidence
        }
        valid_ids = set(evidence_lookup.keys())
        citations = [c for c in citations if c in valid_ids]

        raw_verification = verify_claims(claims, evidence_lookup, overlap_threshold=0.10)

        min_sr = cfg.get("min_support_rate", 0.80)
        answer, citations, enforce_notes = enforce_support_policy(
            answer, citations, raw_verification, min_sr
        )
        notes.extend(enforce_notes)

        claim_details = []
        for rc in raw_verification.get("claims", []):
            excerpt = ""
            for pid in rc.get("citations", []):
                txt = evidence_lookup.get(pid, "")
                if txt:
                    excerpt = txt[:200]
                    break
            claim_details.append(ClaimDetail(
                claim_id=rc.get("claim_id", 0),
                text=rc.get("text", ""),
                citations=rc.get("citations", []),
                supported=rc.get("supported", True),
                support_rationale=rc.get("support_rationale", ""),
                verification_tier=rc.get("verification_tier", 1),
                jaccard=None,
                evidence_excerpt=excerpt,
            ))

        cv = ClaimVerificationResult(
            claims=claim_details,
            supported_claims=raw_verification.get("supported_claims", 0),
            unsupported_claims=raw_verification.get("unsupported_claims", 0),
            support_rate=raw_verification.get("support_rate", 1.0),
        )
        return cv, answer, citations, notes

    def _detect_contradictions(
        self, answer: str, citations: list[str],
        evidence: list[dict], cfg: dict,
    ) -> tuple[list[ContradictionAlert], str, list[str], list[str]]:
        from policy_copilot.verify.contradictions import (
            detect_contradictions,
            apply_contradiction_policy,
        )

        notes: list[str] = []
        raw = detect_contradictions(
            evidence,
            enable_llm=cfg.get("enable_llm_contradictions", False),
        )
        alerts: list[ContradictionAlert] = []
        ev_lookup = {e.get("paragraph_id", ""): e.get("text", "") for e in evidence}

        if raw:
            answer, citations, contra_notes = apply_contradiction_policy(
                answer, citations, raw,
                policy=cfg.get("contradiction_policy", "surface"),
            )
            notes.extend(contra_notes)

            for c in raw:
                pids = c.get("paragraph_ids", [])
                alerts.append(ContradictionAlert(
                    paragraph_ids=pids,
                    rationale=c.get("rationale", ""),
                    confidence=c.get("confidence", "low"),
                    tier=c.get("tier", 1),
                    text_a=ev_lookup.get(pids[0], "") if len(pids) > 0 else "",
                    text_b=ev_lookup.get(pids[1], "") if len(pids) > 1 else "",
                ))

        return alerts, answer, citations, notes

    def _run_critic(self, evidence: list[dict]) -> list[CriticFinding]:
        from policy_copilot.critic.critic_agent import detect_heuristic

        findings: list[CriticFinding] = []
        for ev in evidence:
            text = ev.get("text", "")
            pid = ev.get("paragraph_id", "")
            if not text.strip():
                continue
            result = detect_heuristic(text)
            for label in result.get("labels", []):
                triggers = result.get("rationales", {}).get(label, [])
                findings.append(CriticFinding(
                    label=label,
                    label_name=_LABEL_NAMES.get(label, label),
                    paragraph_id=pid,
                    triggers=triggers if isinstance(triggers, list) else [str(triggers)],
                    rationale=", ".join(triggers) if isinstance(triggers, list) else str(triggers),
                    text_excerpt=text[:300],
                ))
        return findings

    # ----- helpers ---------------------------------------------------------

    def _effective_config(self) -> dict:
        cfg = settings.to_dict()
        cfg["retrieve_k_candidates"] = settings.RETRIEVE_K_CANDIDATES
        cfg["rerank_k_final"] = settings.RERANK_K_FINAL
        cfg["rerank_model"] = settings.RERANK_MODEL
        cfg["abstain_threshold"] = settings.ABSTAIN_THRESHOLD
        cfg["min_support_rate"] = settings.MIN_SUPPORT_RATE
        cfg["enable_llm_contradictions"] = settings.ENABLE_LLM_CONTRADICTIONS
        cfg["contradiction_policy"] = settings.CONTRADICTION_POLICY
        cfg.update(self._overrides)
        return cfg

    @staticmethod
    def _to_evidence_item(e: dict) -> EvidenceItem:
        return EvidenceItem(
            paragraph_id=e.get("paragraph_id", ""),
            doc_id=e.get("doc_id", ""),
            page=e.get("page", 0),
            text=e.get("text", ""),
            source_file=e.get("source_file", ""),
            score_retrieve=round(e.get("score_retrieve", e.get("score", 0.0)), 4),
            score_rerank=round(e.get("score_rerank", 0.0), 4),
            dense_rank=e.get("dense_rank"),
            sparse_rank=e.get("sparse_rank"),
            fused_score=e.get("fused_score"),
            backend=e.get("backend", ""),
        )

    def _build_abstention_result(
        self, question, evidence, confidence, threshold,
        notes, timings, cfg, backend_requested, backend_used, fusion_method,
    ) -> QueryResult:
        timings.total_ms = round(timings.retrieval_ms + timings.rerank_ms, 1)
        return QueryResult(
            question=question,
            answer="INSUFFICIENT_EVIDENCE",
            is_abstained=True,
            abstention_reason="Low confidence: no sufficiently relevant evidence found",
            evidence=[self._to_evidence_item(e) for e in evidence],
            confidence_max_rerank=confidence.get("max_rerank", 0.0),
            confidence_mean_top3=confidence.get("mean_top3_rerank", 0.0),
            abstain_threshold=threshold,
            notes=notes,
            latency=timings,
            backend_requested=backend_requested,
            backend_used=str(backend_used),
            fusion_method=fusion_method,
            config_snapshot=cfg,
        )

    def _build_error_result(
        self, question, evidence, confidence, threshold,
        notes, timings, cfg, backend_requested, backend_used, fusion_method,
    ) -> QueryResult:
        timings.total_ms = round(timings.retrieval_ms + timings.rerank_ms, 1)
        return QueryResult(
            question=question,
            answer="ERROR",
            is_abstained=False,
            evidence=[self._to_evidence_item(e) for e in evidence],
            confidence_max_rerank=confidence.get("max_rerank", 0.0),
            confidence_mean_top3=confidence.get("mean_top3_rerank", 0.0),
            abstain_threshold=threshold,
            notes=notes,
            latency=timings,
            backend_requested=backend_requested,
            backend_used=str(backend_used),
            fusion_method=fusion_method,
            config_snapshot=cfg,
        )
