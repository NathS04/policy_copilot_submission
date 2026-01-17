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

logger = setup_logging()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAFE_FILENAME_RE = re.compile(r"[^\w\s\-.]", re.ASCII)


def _sanitise_filename(name: str) -> str:
    """Return a filesystem-safe version of *name* (no path traversal)."""
    name = Path(name).name  # strip any directory parts
    name = _SAFE_FILENAME_RE.sub("_", name)
    return name or "uploaded.pdf"


def _save_uploaded_files(uploaded_files) -> list[Path]:
    """Persist Streamlit UploadedFile objects to UPLOADS_DIR and return paths."""
    dest_dir = Path(settings.UPLOADS_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for uf in uploaded_files:
