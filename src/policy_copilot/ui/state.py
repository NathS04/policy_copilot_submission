"""
Session state manager for the Streamlit UI.

Centralises all ``st.session_state`` initialisation so that every
view can assume keys exist.  No business logic lives here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

# All views the UI supports
VIEWS = ("ask", "audit", "critic", "experiment", "reviewer")
DEFAULT_VIEW = "ask"


def init_session_state() -> None:
    """Ensure every required session-state key exists with a safe default."""
    defaults: Dict[str, Any] = {
        # Navigation
        "current_view": DEFAULT_VIEW,
        # Chat history — list of {"role": "user"|"assistant", "content": str, "result": QueryResult|None}
        "messages": [],
        # The most recently completed QueryResult (for audit/critic drill-down)
        "selected_result": None,
        # Experiment explorer
        "selected_run_a": None,
        "selected_run_b": None,
        # Corpus stats cache
        "corpus_paragraph_count": 0,
        # Processing flags
        "is_processing": False,
        # Evidence side-panel toggle
        "evidence_panel_open": False,
        # Active claim index for drill-down
        "active_claim_idx": None,
        # Toast notification state
        "toast_message": None,
        "toast_type": None,
        # Reviewer progress tracking  {run_name: set_of_reviewed_qids}
        "reviewer_progress": {},
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ------------------------------------------------------------------ #
#  Convenience helpers                                                 #
# ------------------------------------------------------------------ #

def switch_view(view: str) -> None:
    if view in VIEWS:
        st.session_state["current_view"] = view


def get_view() -> str:
    return st.session_state.get("current_view", DEFAULT_VIEW)


def append_user_message(content: str) -> None:
    st.session_state["messages"].append({
        "role": "user",
        "content": content,
        "result": None,
    })


def append_assistant_message(content: str, result: Any = None) -> None:
    st.session_state["messages"].append({
        "role": "assistant",
        "content": content,
        "result": result,
    })


def get_messages() -> List[Dict[str, Any]]:
    return st.session_state.get("messages", [])


def get_last_result() -> Optional[Any]:
    """Return the QueryResult attached to the most recent assistant message."""
    for msg in reversed(get_messages()):
        if msg.get("role") == "assistant" and msg.get("result") is not None:
            return msg["result"]
    return None


def set_selected_result(result: Any) -> None:
    st.session_state["selected_result"] = result


def get_selected_result() -> Optional[Any]:
    return st.session_state.get("selected_result")


def clear_chat() -> None:
    st.session_state["messages"] = []
    st.session_state["selected_result"] = None
