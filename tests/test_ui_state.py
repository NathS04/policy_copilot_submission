"""
Tests for UI session state management.

These tests do NOT import Streamlit directly — they test the pure
logic by mocking ``st.session_state`` as a plain dict.
"""
import pytest
from unittest.mock import patch, MagicMock


# We mock streamlit before importing the state module
@pytest.fixture(autouse=True)
def mock_streamlit():
    """Replace st.session_state with a plain dict for testing."""
    mock_st = MagicMock()
    mock_st.session_state = {}
    with patch.dict("sys.modules", {"streamlit": mock_st}):
        yield mock_st


# ------------------------------------------------------------------ #
#  Tests: init_session_state                                           #
# ------------------------------------------------------------------ #

class TestInitSessionState:

    def test_initialises_all_keys(self, mock_streamlit):
        from policy_copilot.ui.state import init_session_state

        init_session_state()

        state = mock_streamlit.session_state
        assert "current_view" in state
        assert "messages" in state
        assert "selected_result" in state
        assert "is_processing" in state

    def test_defaults_to_ask_view(self, mock_streamlit):
        from policy_copilot.ui.state import init_session_state

        init_session_state()

        assert mock_streamlit.session_state["current_view"] == "ask"

    def test_does_not_overwrite_existing(self, mock_streamlit):
        mock_streamlit.session_state["current_view"] = "audit"

        from policy_copilot.ui.state import init_session_state
        init_session_state()

        assert mock_streamlit.session_state["current_view"] == "audit"


# ------------------------------------------------------------------ #
#  Tests: view switching                                               #
# ------------------------------------------------------------------ #

class TestViewSwitching:

    def test_switch_view(self, mock_streamlit):
        from policy_copilot.ui.state import init_session_state, switch_view, get_view

        init_session_state()
        switch_view("critic")

        assert get_view() == "critic"

    def test_switch_view_ignores_invalid(self, mock_streamlit):
        from policy_copilot.ui.state import init_session_state, switch_view, get_view

        init_session_state()
        switch_view("nonexistent_view")

        assert get_view() == "ask"


# ------------------------------------------------------------------ #
#  Tests: message management                                           #
# ------------------------------------------------------------------ #

class TestMessageManagement:

    def test_append_user_message(self, mock_streamlit):
        from policy_copilot.ui.state import init_session_state, append_user_message, get_messages

        init_session_state()
        append_user_message("Hello")

        msgs = get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hello"

    def test_append_assistant_message_with_result(self, mock_streamlit):
        from policy_copilot.ui.state import (
            init_session_state, append_assistant_message, get_messages, get_last_result,
        )

        init_session_state()
        mock_result = {"answer": "Test answer"}
        append_assistant_message("The answer is...", result=mock_result)

        msgs = get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "assistant"
        assert msgs[0]["result"] == mock_result

        assert get_last_result() == mock_result

    def test_clear_chat(self, mock_streamlit):
        from policy_copilot.ui.state import (
            init_session_state, append_user_message, clear_chat, get_messages,
        )

        init_session_state()
        append_user_message("Test")
        clear_chat()

        assert get_messages() == []


# ------------------------------------------------------------------ #
#  Tests: selected result                                              #
# ------------------------------------------------------------------ #

class TestSelectedResult:

    def test_set_and_get_selected_result(self, mock_streamlit):
        from policy_copilot.ui.state import (
            init_session_state, set_selected_result, get_selected_result,
        )

        init_session_state()
        mock_result = {"query_id": "abc123"}
        set_selected_result(mock_result)

        assert get_selected_result() == mock_result

    def test_selected_result_default_none(self, mock_streamlit):
        from policy_copilot.ui.state import init_session_state, get_selected_result

        init_session_state()
        assert get_selected_result() is None
