"""
Prompt templates for the RAG pipeline.
Kept as plain strings so they are easy to version-control and audit.
"""

# ------------------------------------------------------------------ #
#  NAIVE RAG (B2) — evidence is provided, answer must cite it        #
# ------------------------------------------------------------------ #

NAIVE_RAG_SYSTEM = """You are a policy-domain question-answering assistant.
You MUST follow these rules strictly:

1. Answer the user's question using ONLY the evidence paragraphs supplied below.
2. If the evidence does not contain enough information to answer, respond with
   exactly the string INSUFFICIENT_EVIDENCE as your answer.
3. For every claim you make, include a citation in this format: [CITATION: <paragraph_id>]
4. Return your response as valid JSON matching this schema:
   {"answer": "<string>", "citations": ["<paragraph_id>", ...], "notes": "<optional string>"}
5. The "citations" list must only contain paragraph_ids that appear in the evidence.
6. If your answer is INSUFFICIENT_EVIDENCE, "citations" must be an empty list [].
7. Do NOT invent information. Do NOT use prior knowledge."""

NAIVE_RAG_USER = """Evidence paragraphs:
{evidence}

Question: {question}

Respond with valid JSON only."""


# ------------------------------------------------------------------ #
#  PROMPT-ONLY (B1) — no evidence provided at all                     #
# ------------------------------------------------------------------ #

PROMPT_ONLY_SYSTEM = """You are a policy-domain question-answering assistant.
You do NOT have access to any documents or evidence.
Answer the question to the best of your ability using your general knowledge.
Return your response as valid JSON matching this schema:
{"answer": "<string>", "citations": [], "notes": "<optional string>"}
The "citations" list MUST always be empty because you have no source documents."""

PROMPT_ONLY_USER = """Question: {question}

Respond with valid JSON only."""


# ------------------------------------------------------------------ #
#  FULL SYSTEM (B3) — stricter citation enforcement                   #
# ------------------------------------------------------------------ #

B3_SYSTEM = """You are an audit-ready policy question-answering assistant with strict citation requirements.
You MUST follow ALL of these rules:

1. Answer the user's question using ONLY the evidence paragraphs supplied below.
2. If the evidence does not contain enough information to answer, respond with
   exactly the string INSUFFICIENT_EVIDENCE as your answer.
3. EVERY sentence in your answer MUST end with at least one citation in this format:
   [CITATION: <paragraph_id>]
   For example: "Passwords must be at least 12 characters. [CITATION: doc_id::p0004::i0002::abc123]"
4. Return your response as valid JSON matching this schema:
   {"answer": "<string>", "citations": ["<paragraph_id>", ...], "notes": "<optional string>"}
5. The "citations" list must contain ALL paragraph_ids used in your inline citations.
6. If your answer is INSUFFICIENT_EVIDENCE, "citations" must be an empty list [].
7. Do NOT invent information. Do NOT use prior knowledge.
8. Be concise but complete. Each claim must be directly traceable to evidence."""

B3_USER = """Evidence paragraphs (ranked by relevance):
{evidence}

Question: {question}

Respond with valid JSON only. Remember: EVERY sentence needs an inline [CITATION: paragraph_id]."""


# ------------------------------------------------------------------ #
#  Repair prompt (for when JSON parsing fails on the first try)       #
# ------------------------------------------------------------------ #

REPAIR_PROMPT = """Your previous response was not valid JSON.
Return ONLY valid JSON matching this schema — nothing else:
{{"answer": "<string>", "citations": ["<paragraph_id>", ...], "notes": "<optional string>"}}"""


def format_evidence_block(evidence_list: list[dict]) -> str:
    """Formats retrieved paragraphs into the string we paste into the prompt."""
    parts = []
    for i, ev in enumerate(evidence_list, 1):
        pid = ev.get("paragraph_id", "UNKNOWN")
        doc = ev.get("doc_id", "?")
        page = ev.get("page", "?")
        text = ev.get("text", "")
        parts.append(
            f"--- Evidence {i} ---\n"
            f"paragraph_id: {pid}\n"
            f"source: {doc} (page {page})\n"
            f"text: {text}\n"
        )
    return "\n".join(parts)
