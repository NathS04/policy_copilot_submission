"""
LLM answerer that supports OpenAI and Anthropic providers.
Handles JSON parsing, repair retries, and citation validation.
Supports B1 (prompt-only), B2 (naive RAG), and B3 (full system).
"""
import json
import time
from typing import Optional

from policy_copilot.config import settings
import re as _re
from policy_copilot.generate.schema import RAGResponse, make_llm_disabled, make_insufficient
from policy_copilot.generate.prompts import (
    NAIVE_RAG_SYSTEM, NAIVE_RAG_USER,
    PROMPT_ONLY_SYSTEM, PROMPT_ONLY_USER,
    B3_SYSTEM, B3_USER,
    REPAIR_PROMPT, format_evidence_block,
)
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


# ------------------------------------------------------------------ #
#  Provider helpers                                                    #
# ------------------------------------------------------------------ #

def _call_openai(system: str, user: str, model: str, temperature: float,
                 max_tokens: int) -> tuple[str, dict]:
    """Returns (raw_text, usage_meta)."""
    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        seed=settings.SEED,
    )
    text = resp.choices[0].message.content or ""
    usage = {
        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
        "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
    }
    return text.strip(), usage


def _call_anthropic(system: str, user: str, model: str, temperature: float,
                    max_tokens: int) -> tuple[str, dict]:
    """Returns (raw_text, usage_meta)."""
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text if resp.content else ""
    usage = {
        "prompt_tokens": getattr(resp.usage, "input_tokens", 0),
        "completion_tokens": getattr(resp.usage, "output_tokens", 0),
    }
    return text.strip(), usage


def _call_llm(system: str, user: str) -> tuple[str, dict, float]:
    """Dispatches to correct provider. Returns (text, usage, latency_ms)."""
    provider = settings.PROVIDER.lower()
    model = settings.LLM_MODEL
    temp = settings.TEMPERATURE
    maxt = settings.MAX_TOKENS

    t0 = time.time()

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            return "", {}, 0.0
        text, usage = _call_openai(system, user, model, temp, maxt)
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            return "", {}, 0.0
        text, usage = _call_anthropic(system, user, model, temp, maxt)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    latency = (time.time() - t0) * 1000
    logger.info(f"LLM call ({provider}/{model}) took {latency:.0f}ms")
    return text, usage, latency


# ------------------------------------------------------------------ #
#  JSON parsing + repair                                               #
# ------------------------------------------------------------------ #

def _parse_json_response(raw: str) -> Optional[dict]:
    """Try to parse the LLM output as JSON. Strips markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        # remove markdown code fences
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _attempt_repair(original_response: str) -> Optional[dict]:
    """Send a repair prompt to get valid JSON."""
    logger.warning("JSON parse failed, attempting repair prompt...")
    text, _, _ = _call_llm(REPAIR_PROMPT, original_response)
    return _parse_json_response(text)


# ------------------------------------------------------------------ #
#  Citation validation                                                 #
# ------------------------------------------------------------------ #

def _validate_citations(response: RAGResponse, valid_ids: set[str]) -> RAGResponse:
    """Remove citations not in the evidence set; add notes if needed."""
    notes_parts = []
    if response.notes:
        notes_parts.append(response.notes)

    if response.answer != "INSUFFICIENT_EVIDENCE":
        # filter invalid citations
        clean = [c for c in response.citations if c in valid_ids]
        removed = [c for c in response.citations if c not in valid_ids]
        if removed:
            logger.warning(f"Removed invalid citations: {removed}")
            notes_parts.append("INVALID_CITATIONS_REMOVED")
        response.citations = clean

        # warn if no citations given for a real answer
        if not response.citations:
            notes_parts.append("NO_CITATIONS_GIVEN")
    else:
        # INSUFFICIENT_EVIDENCE must have empty citations
        response.citations = []

    response.notes = "; ".join(notes_parts) if notes_parts else None
    return response


# ------------------------------------------------------------------ #
#  Relevance gate for extractive fallback                              #
# ------------------------------------------------------------------ #

_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "and", "but", "or", "nor", "not", "no", "so", "if", "then", "than",
    "that", "this", "these", "those", "what", "which", "who", "whom",
    "how", "when", "where", "why", "its", "his", "her", "their", "our",
    "for", "from", "into", "with", "about", "between", "through", "during",
    "before", "after", "above", "below", "to", "of", "in", "on", "at", "by",
    "all", "each", "every", "any", "few", "more", "most", "some", "such",
})


def _is_relevant_to_question(question: str, paragraph_text: str) -> bool:
    """Lightweight keyword-overlap check: >= 2 overlaps or >= 25% ratio."""
    def _keywords(text):
        return {w for w in _re.findall(r"[a-z0-9]+", text.lower())
                if len(w) >= 3 and w not in _STOP_WORDS}
    q_kw = _keywords(question)
    p_kw = _keywords(paragraph_text)
    if not q_kw:
        return True
    overlap = q_kw & p_kw
    return len(overlap) >= 2 or (len(overlap) / len(q_kw)) >= 0.25


# ------------------------------------------------------------------ #
#  Public API                                                          #
# ------------------------------------------------------------------ #

class Answerer:
    """Stateless answerer — call generate() for each query."""

    def _check_llm_available(self) -> bool:
        """Returns False if LLM is disabled or no key is set."""
        if not settings.ENABLE_LLM:
            return False
        provider = settings.PROVIDER.lower()
        if provider == "openai" and not settings.OPENAI_API_KEY:
            return False
        if provider == "anthropic" and not settings.ANTHROPIC_API_KEY:
            return False
        return True

    def generate_naive_rag(self, question: str, evidence: list[dict],
                           allow_fallback: bool = False) -> tuple[RAGResponse, dict]:
        """
        B2 Naive RAG: retrieve top-k, send to LLM, parse JSON answer.
        Returns (RAGResponse, metadata_dict).
        """
        if not self._check_llm_available():
            if allow_fallback and evidence:
                return self._extractive_fallback(evidence[0])
            return make_llm_disabled(), {"latency_ms": 0}

        evidence_block = format_evidence_block(evidence)
        user_msg = NAIVE_RAG_USER.format(evidence=evidence_block, question=question)

        raw, usage, latency = _call_llm(NAIVE_RAG_SYSTEM, user_msg)

        parsed = _parse_json_response(raw)
        if parsed is None:
            parsed = _attempt_repair(raw)
        if parsed is None:
            logger.error("Could not parse LLM response as JSON even after repair")
            resp = RAGResponse(answer=raw[:500], citations=[], notes="JSON_PARSE_FAILED")
        else:
            resp = RAGResponse(**{k: parsed.get(k) for k in ("answer", "citations", "notes") if k in parsed})

        valid_ids = {e["paragraph_id"] for e in evidence if "paragraph_id" in e}
        resp = _validate_citations(resp, valid_ids)

        meta = {"latency_ms": latency, "usage": usage, "raw_response": raw,
                "provider": settings.PROVIDER, "model": settings.LLM_MODEL}
        return resp, meta

    def generate_prompt_only(self, question: str) -> tuple[RAGResponse, dict]:
        """
        B1 Prompt-only: no evidence, just the question.
        """
        if not self._check_llm_available():
            return make_llm_disabled(), {"latency_ms": 0}

        user_msg = PROMPT_ONLY_USER.format(question=question)
        raw, usage, latency = _call_llm(PROMPT_ONLY_SYSTEM, user_msg)

        parsed = _parse_json_response(raw)
        if parsed is None:
            parsed = _attempt_repair(raw)
        if parsed is None:
            resp = RAGResponse(answer=raw[:500], citations=[], notes="JSON_PARSE_FAILED")
        else:
            resp = RAGResponse(**{k: parsed.get(k) for k in ("answer", "citations", "notes") if k in parsed})

        # prompt-only must never have citations
        resp.citations = []

        meta = {"latency_ms": latency, "usage": usage, "raw_response": raw,
                "provider": settings.PROVIDER, "model": settings.LLM_MODEL}
        return resp, meta

    def generate_b3(self, question: str, evidence: list[dict],
                    allow_fallback: bool = False) -> tuple[RAGResponse, dict]:
        """
        B3 Full System: stricter citation enforcement prompts.
        Returns (RAGResponse, metadata_dict).
        If LLM available and not fallback: call LLM, parse JSON, return Response.
        Else (extractive or no LLM): use _extractive_fallback.
        """
        if not self._check_llm_available():
            if allow_fallback and evidence:
                return self._gated_extractive_fallback(question, evidence[0])
            return make_llm_disabled(), {"latency_ms": 0, "fallback_used": False}

        if allow_fallback and evidence:
            return self._gated_extractive_fallback(question, evidence[0])

        # LLM path: call LLM, parse JSON, validate, return
        evidence_block = format_evidence_block(evidence)
        user_msg = B3_USER.format(evidence=evidence_block, question=question)

        raw, usage, latency = _call_llm(B3_SYSTEM, user_msg)

        parsed = _parse_json_response(raw)
        if parsed is None:
            parsed = _attempt_repair(raw)
        if parsed is None:
            logger.error("Could not parse B3 LLM response as JSON")
            resp = RAGResponse(answer=raw[:500], citations=[], notes="JSON_PARSE_FAILED")
        else:
            cites = parsed.get("citations", [])
            cleaned_cites = []
            if isinstance(cites, list):
                for c in cites:
                    if isinstance(c, dict) and "paragraph_id" in c:
                        cleaned_cites.append(str(c["paragraph_id"]))
                    elif isinstance(c, str):
                        cleaned_cites.append(c)
            parsed["citations"] = cleaned_cites
            resp = RAGResponse(**{k: parsed.get(k) for k in ("answer", "citations", "notes") if k in parsed})

        valid_ids = {e["paragraph_id"] for e in evidence if "paragraph_id" in e}
        resp = _validate_citations(resp, valid_ids)

        tokens = 0
        if isinstance(usage, dict):
            tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        meta = {
            "latency_ms": latency,
            "usage": usage,
            "raw_response": raw,
            "provider": settings.PROVIDER,
            "model": settings.LLM_MODEL,
            "fallback_used": False,
            "confidence": getattr(resp, "confidence", None) or 1.0,
            "tokens": tokens,
        }
        return resp, meta

    def _gated_extractive_fallback(self, question: str, top_evidence: dict) -> tuple[RAGResponse, dict]:
        """B3 extractive with relevance gate: abstain if evidence is irrelevant to question."""
        text = top_evidence.get("text", "")
        if not _is_relevant_to_question(question, text):
            resp = make_insufficient()
            resp.notes = "FALLBACK_RELEVANCE_FAIL"
            return resp, {"latency_ms": 0, "fallback_used": True}
        return self._extractive_fallback(top_evidence)

    def _extractive_fallback(self, top_evidence: dict) -> tuple[RAGResponse, dict]:
        """
        Returns the top paragraph text with [CITATION: pid] per sentence so that
        claim_split yields citations per claim (citation before period so it stays with sentence).
        """
        import re
        text = top_evidence.get("text", "")[:2000]
        pid = top_evidence.get("paragraph_id", "")
        sentences = re.split(r'(?<=[.?!])\s+', text)
        # Put [CITATION: pid] before the trailing .!? so split_claims attaches it to the same claim
        annotated_sentences = []
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if s[-1] in ".!?":
                annotated_sentences.append(f"{s[:-1]} [CITATION: {pid}]{s[-1]}")
            else:
                annotated_sentences.append(f"{s} [CITATION: {pid}].")
        answer = " ".join(annotated_sentences)
        resp = RAGResponse(
            answer=answer,
            citations=[pid] if pid else [],
            notes="EXTRACTIVE_FALLBACK",
        )
        return resp, {"latency_ms": 0, "fallback_used": True}
