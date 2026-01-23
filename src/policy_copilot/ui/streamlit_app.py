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
        safe_name = _sanitise_filename(uf.name)
        target = dest_dir / safe_name
        # Avoid silent overwrites – add a numeric suffix if needed
        counter = 1
        stem, suffix = target.stem, target.suffix
        while target.exists():
            target = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        target.write_bytes(uf.getbuffer())
        saved.append(target)
    return saved


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Policy Copilot", page_icon="📜", layout="wide")

# ---------------------------------------------------------------------------
# Sidebar – Upload PDFs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📂 Add Documents")
    uploaded = st.file_uploader(
        "Upload one or more PDFs to add to the corpus.",
        type=["pdf"],
        accept_multiple_files=True,
    )

    process_btn = st.button(
        "Process & Add to Corpus",
        disabled=not uploaded,
        use_container_width=True,
    )

    if process_btn and uploaded:
        with st.spinner("Saving files & ingesting…"):
            try:
                saved_paths = _save_uploaded_files(uploaded)

                # Lazy-import so the app still starts even if scripts/ isn't
                # on the path yet (we added _PROJECT_ROOT above).
                sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))
                from ingest_corpus import ingest_pdfs
                from build_index import build_index

                n = ingest_pdfs(
                    pdf_paths=saved_paths,
                    output_dir=Path(settings.CORPUS_DIR),
                    manifest_path=Path(settings.MANIFEST_PATH),
                    append=True,
                )

                build_index(
                    input_path=Path(settings.CORPUS_JSONL),
                    index_dir=Path(settings.INDEX_DIR),
                )

                # Invalidate any cached retriever so the next query picks
                # up the new index.
