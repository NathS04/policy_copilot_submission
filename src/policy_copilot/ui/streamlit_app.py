"""
Policy Copilot — Streamlit UI (Application Shell)

Thin entry-point that wires together:
  - page config and session state
  - global CSS from the design system
  - sidebar navigation, branding, and document upload
  - view routing to per-mode renderers

All rendering logic lives in ``renderers.py``, all visual tokens in
``theme.py``, all reusable widgets in ``components.py``.  Business
logic lives in ``policy_copilot.service``.
"""
from __future__ import annotations

import re
import sys
import traceback
from pathlib import Path

import streamlit as st

# Ensure project root is on sys.path for script-level imports
_SRC_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _SRC_DIR.parent
for _p in (_SRC_DIR, _PROJECT_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from policy_copilot.config import settings                                     # noqa: E402
from policy_copilot.logging_utils import setup_logging                         # noqa: E402
from policy_copilot.ui.state import (                                          # noqa: E402
    clear_chat, get_view, init_session_state, switch_view,
)
from policy_copilot.ui.theme import ICONS, inject_global_css                   # noqa: E402
from policy_copilot.ui.renderers import (                                      # noqa: E402
    render_ask_view,
    render_audit_trace_view,
    render_critic_lens_view,
    render_experiment_explorer_view,
    render_reviewer_view,
)

logger = setup_logging()

_SAFE_FILENAME_RE = re.compile(r"[^\w\s\-.]", re.ASCII)


# ================================================================== #
#  Helper functions (defined before top-level sidebar code)            #
# ================================================================== #

def _process_uploads(uploaded_files):
    """Save uploaded PDFs, ingest, and rebuild index."""
    with st.spinner("Processing documents..."):
        try:
            dest_dir = Path(settings.UPLOADS_DIR)
            dest_dir.mkdir(parents=True, exist_ok=True)
            saved = []
            for uf in uploaded_files:
                safe_name = _SAFE_FILENAME_RE.sub("_", Path(uf.name).name) or "uploaded.pdf"
                target = dest_dir / safe_name
                counter = 1
                stem, suffix = target.stem, target.suffix
                while target.exists():
                    target = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                target.write_bytes(uf.getbuffer())
                saved.append(target)

            sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))
            from ingest_corpus import ingest_pdfs
            from build_index import build_index

            n = ingest_pdfs(
                pdf_paths=saved,
                output_dir=Path(settings.CORPUS_DIR),
                manifest_path=Path(settings.MANIFEST_PATH),
                append=True,
            )
            build_index(
                input_path=Path(settings.CORPUS_JSONL),
                index_dir=Path(settings.INDEX_DIR),
            )
            st.cache_resource.clear()
            st.success(f"Added {n} paragraph(s) from {len(saved)} PDF(s).")
        except Exception:
            logger.error(traceback.format_exc())
            st.error("Processing failed. Check server logs.")


@st.cache_resource
def _get_retriever():
    """Lazily build the best available retriever (hybrid preferred)."""
    from policy_copilot.retrieve.retriever import Retriever
    dense = Retriever(backend="dense")

    try:
        from policy_copilot.retrieve.bm25_retriever import BM25Retriever
        bm25 = BM25Retriever()
        sparse_ok = bm25.is_ready
    except Exception:
        bm25 = None
        sparse_ok = False

    if dense.loaded and sparse_ok:
        from policy_copilot.retrieve.hybrid import HybridRetriever
        return HybridRetriever(dense, bm25)

    return dense


def _get_orchestrator():
    from policy_copilot.service.chat_orchestrator import ChatOrchestrator
    return ChatOrchestrator(retriever=_get_retriever())


def _export_audit_report(result):
    """Generate and offer download of audit report."""
    from policy_copilot.service.audit_report_service import AuditReportService
    report = AuditReportService.generate_report(result)

    col_j, col_h, col_m = st.columns(3)
    col_j.download_button(
        f"{ICONS['export']} Download JSON",
        data=AuditReportService.to_json(report),
        file_name=f"audit_report_{result.query_id}.json",
        mime="application/json",
        use_container_width=True,
    )
    col_h.download_button(
        f"{ICONS['export']} Download HTML",
        data=AuditReportService.to_html(report),
        file_name=f"audit_report_{result.query_id}.html",
        mime="text/html",
        use_container_width=True,
    )
    col_m.download_button(
        f"{ICONS['export']} Download Markdown",
        data=AuditReportService.to_markdown(report),
        file_name=f"audit_report_{result.query_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )


# ================================================================== #
#  Page config + state + CSS                                           #
# ================================================================== #

st.set_page_config(
    page_title="Policy Copilot",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_global_css()


# ================================================================== #
#  Sidebar                                                             #
# ================================================================== #

with st.sidebar:
    st.markdown(
        '<div class="pc-sidebar-brand">'
        "<h2>Policy Copilot</h2>"
        "<p>Audit-Ready Policy Assistant</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="pc-sidebar-divider">', unsafe_allow_html=True)

    # View selector
    _VIEW_LABELS = {
        "ask":        f'{ICONS["search"]}  Ask',
        "audit":      f'{ICONS["document"]}  Audit Trace',
        "critic":     f'{ICONS["shield"]}  Critic Lens',
        "experiment": f'{ICONS["chart"]}  Experiment Explorer',
        "reviewer":   f'{ICONS["pencil"]}  Reviewer Mode',
    }

    current = get_view()
    selected_view = st.radio(
        "Navigation",
        list(_VIEW_LABELS.keys()),
        format_func=lambda v: _VIEW_LABELS[v],
        index=list(_VIEW_LABELS.keys()).index(current),
        key="view_radio",
        label_visibility="collapsed",
    )
    if selected_view != current:
        switch_view(selected_view)
        st.rerun()

    st.markdown('<hr class="pc-sidebar-divider">', unsafe_allow_html=True)

    # Document upload
    st.markdown("##### Add Documents")
    uploaded = st.file_uploader(
        "Upload PDFs to the corpus",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if st.button("Process & Index", disabled=not uploaded, use_container_width=True):
        _process_uploads(uploaded)

    # Corpus stats
    jsonl = Path(settings.CORPUS_JSONL)
    if jsonl.exists():
        count = sum(1 for _ in open(jsonl, encoding="utf-8"))
        st.caption(f"Corpus: **{count}** paragraphs")

    st.markdown('<hr class="pc-sidebar-divider">', unsafe_allow_html=True)

    # Chat controls
    if get_view() == "ask":
        if st.button("Clear Chat", use_container_width=True):
            clear_chat()
            st.rerun()


# ================================================================== #
#  Router                                                              #
# ================================================================== #

view = get_view()

if view == "ask":
    render_ask_view(_get_retriever, _get_orchestrator, _export_audit_report)
elif view == "audit":
    render_audit_trace_view(_export_audit_report)
elif view == "critic":
    render_critic_lens_view()
elif view == "experiment":
    render_experiment_explorer_view()
elif view == "reviewer":
    render_reviewer_view()
else:
    render_ask_view(_get_retriever, _get_orchestrator, _export_audit_report)


# ================================================================== #
#  Entry point                                                         #
# ================================================================== #

def main():
    """Entry-point when invoked as ``python -m policy_copilot.ui.streamlit_app``."""
    pass


if __name__ == "__main__":
    main()
