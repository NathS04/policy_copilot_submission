"""
Pydantic models for the RAG answer output.
Every baseline and the full system share this schema so evaluation is uniform.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class RAGResponse(BaseModel):
    """Structured output that every pipeline variant must produce."""
    answer: str = Field(..., description="The answer text, or INSUFFICIENT_EVIDENCE")
    citations: List[str] = Field(default_factory=list, description="List of paragraph_ids cited")
    notes: Optional[str] = Field(default=None, description="Any warnings or processing notes")


# ---- helpers ----

def make_insufficient() -> RAGResponse:
    return RAGResponse(answer="INSUFFICIENT_EVIDENCE", citations=[], notes=None)

def make_llm_disabled() -> RAGResponse:
    return RAGResponse(answer="LLM_DISABLED", citations=[], notes="No API key configured")
