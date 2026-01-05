"""
LLM-based judges for Tier-2 claim verification and contradiction detection.
Each function calls the configured LLM provider with strict JSON prompts.
Results are cached to JSONL files for reproducibility and cost control.
"""
import hashlib
import json
from pathlib import Path
from typing import Optional

from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


# ------------------------------------------------------------------ #
#  Caching                                                             #
# ------------------------------------------------------------------ #

def _cache_key(*parts: str) -> str:
    """Deterministic hash from multiple string parts."""
    combined = "||".join(str(p) for p in parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def _load_cache(cache_path: Path) -> dict[str, dict]:
    """Load JSONL cache into memory keyed by cache_key."""
    cache = {}
    if cache_path.exists():
        with open(cache_path, "r") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    cache[obj.get("_cache_key", "")] = obj
                except json.JSONDecodeError:
                    pass
    return cache


def _append_cache(cache_path: Path, entry: dict):
    """Append one entry to JSONL cache."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ------------------------------------------------------------------ #
#  LLM call helper                                                     #
# ------------------------------------------------------------------ #

def _call_llm(system: str, user: str) -> str:
    """Call the configured LLM provider and return raw text."""
    provider = settings.PROVIDER.lower()
    model = settings.LLM_MODEL
    temperature = settings.TEMPERATURE
    max_tokens = settings.MAX_TOKENS

    if provider == "openai":
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
        return (resp.choices[0].message.content or "").strip()
    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
        )
        return resp.content[0].text.strip()
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


# ------------------------------------------------------------------ #
#  Tier-2 Claim Support Judge                                          #
# ------------------------------------------------------------------ #

_CLAIM_VERIFY_SYSTEM = """You are a strict fact-checking assistant.
You will receive a CLAIM and one or more EVIDENCE paragraphs.
Your task: determine if the evidence EXPLICITLY supports the claim.

Rules:
1. "supported=true" ONLY if the paragraph text explicitly supports the claim.
2. You MUST provide a "quote" that is an EXACT substring from the evidence text that proves support.
3. If no evidence supports the claim, return supported=false.
4. Return ONLY valid JSON, no other text.

Output format:
{"supported": true, "rationale": "short explanation", "quote": "exact substring from evidence"}
"""

_CLAIM_VERIFY_USER = """CLAIM: {claim}

EVIDENCE:
{evidence}

Return JSON only:"""


def llm_verify_claim(claim_text: str, cited_paragraph_texts: list[str],
                     cache_dir: Optional[Path] = None,
                     query_id: str = "", claim_id: str = "") -> dict:
    """
    LLM-based claim verification.
    Returns: {supported: bool, rationale: str, quote: str}
    Falls back to empty dict on error (caller should use Tier-1 heuristic).
    """
    # cache key
    pids_hash = _cache_key(*cited_paragraph_texts)
    key = _cache_key(query_id, claim_id, pids_hash)

    # check cache
    if cache_dir:
        cache_path = cache_dir / "llm_claim_verify.jsonl"
        cache = _load_cache(cache_path)
        if key in cache:
            logger.debug(f"LLM claim verify cache hit: {key}")
            return cache[key]

    # build prompt
    evidence_block = "\n---\n".join(
        f"Paragraph {i+1}:\n{text}" for i, text in enumerate(cited_paragraph_texts)
    )
    user = _CLAIM_VERIFY_USER.format(claim=claim_text, evidence=evidence_block)

    try:
        raw = _call_llm(_CLAIM_VERIFY_SYSTEM, user)
        result = _parse_json_response(raw)
        if "supported" not in result:
            logger.warning(f"LLM claim verify missing 'supported' key: {raw[:100]}")
            return {}
    except Exception as e:
        logger.error(f"LLM claim verify failed: {e}")
        return {}

    # cache result
    result["_cache_key"] = key
    result["query_id"] = query_id
    result["claim_id"] = claim_id
    if cache_dir:
        _append_cache(cache_path, result)

    return result


# ------------------------------------------------------------------ #
#  Tier-2 Contradiction Judge                                          #
# ------------------------------------------------------------------ #

_CONTRADICTION_SYSTEM = """You are a contradiction detection assistant.
You will receive TWO evidence paragraphs from a policy corpus.
Determine if they CONTRADICT each other.

Rules:
1. A contradiction exists only if the two paragraphs make INCOMPATIBLE claims.
2. Mere differences in scope or topic are NOT contradictions.
3. Return ONLY valid JSON, no other text.

Output format:
{"contradiction": true, "rationale": "explanation of the conflict"}
"""

_CONTRADICTION_USER = """PARAGRAPH A (ID: {id_a}):
{text_a}

PARAGRAPH B (ID: {id_b}):
{text_b}

Return JSON only:"""


def llm_judge_contradiction(paragraph_a: dict, paragraph_b: dict,
                            cache_dir: Optional[Path] = None) -> dict:
    """
    LLM-based contradiction judge.
    Returns: {contradiction: bool, rationale: str}
    Falls back to empty dict on error.
    """
    id_a = paragraph_a.get("paragraph_id", "")
    id_b = paragraph_b.get("paragraph_id", "")
    text_a = paragraph_a.get("text", "")
    text_b = paragraph_b.get("text", "")

    key = _cache_key(id_a, id_b)

    # check cache
    if cache_dir:
        cache_path = cache_dir / "llm_contradictions.jsonl"
        cache = _load_cache(cache_path)
        if key in cache:
            logger.debug(f"LLM contradiction cache hit: {key}")
            return cache[key]

    user = _CONTRADICTION_USER.format(
        id_a=id_a, text_a=text_a, id_b=id_b, text_b=text_b
    )

    try:
        raw = _call_llm(_CONTRADICTION_SYSTEM, user)
        result = _parse_json_response(raw)
        if "contradiction" not in result:
            logger.warning(f"LLM contradiction missing 'contradiction' key: {raw[:100]}")
            return {}
    except Exception as e:
        logger.error(f"LLM contradiction judge failed: {e}")
        return {}

    # cache
    result["_cache_key"] = key
    result["paragraph_id_a"] = id_a
    result["paragraph_id_b"] = id_b
    if cache_dir:
        _append_cache(cache_path, result)

    return result
