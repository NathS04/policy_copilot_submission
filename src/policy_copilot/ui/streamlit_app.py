"""
Policy Copilot – Streamlit UI
Provides:
  • Q&A interface (question → retrieve → generate)
  • Sidebar for uploading PDFs into the corpus
"""

import re
import sys
import traceback
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so script-level imports work
# when running with `streamlit run …` from the repo root.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[4]  # …/policy_copilot_submission
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging
