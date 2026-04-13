"""
Per-mode rendering orchestrators for the Policy Copilot UI.

Each ``render_*_view`` function composes primitives from ``components.py``
into a full page layout.  Business-logic callables (orchestrator, retriever,
services) are passed in as arguments — renderers never import the service
layer directly.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

import streamlit as st

from policy_copilot.service.schemas import CriticFinding, QueryResult
from policy_copilot.ui.components import (
    render_abstention_banner,
    render_chat_empty_state,
    render_citation_pills,
    render_claim_verification_table,
    render_confidence_badge,
    render_contradiction_alert,
    render_contradiction_section,
    render_critic_findings,
    render_empty_state,
    render_evidence_rail,
    render_latency_breakdown,
    render_metadata_panel,
    render_progress_indicator,
    render_status_banner,
    render_view_header,
)
from policy_copilot.ui.state import (
    append_assistant_message,
    append_user_message,
    get_messages,
    get_selected_result,
    set_selected_result,
    switch_view,
)
from policy_copilot.ui.theme import (
    COLOURS,
    ICONS,
    badge_html,
    section_header,
)


# ================================================================== #
#  VIEW: Ask                                                           #
# ================================================================== #

def render_ask_view(
    get_retriever: Callable,
    get_orchestrator: Callable,
    export_report_fn: Callable,
) -> None:
    """Full Ask-mode layout: welcome state, chat history, input."""
    render_view_header("Ask", "Evidence-grounded answers with inline citations")

    messages = get_messages()

    if not messages:
        selected_prompt = render_chat_empty_state()
        if selected_prompt:
            _handle_query(selected_prompt, get_retriever, get_orchestrator)
            st.rerun()
        # Early return — nothing else to show
        return

    # Render chat history
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            result = msg.get("result")
            if result is not None and msg["role"] == "assistant":
                _render_answer_footer(result, export_report_fn)

    # Chat input
    if prompt := st.chat_input("Ask a policy question..."):
        _handle_query(prompt, get_retriever, get_orchestrator)
        st.rerun()


def _handle_query(
    question: str,
    get_retriever: Callable,
    get_orchestrator: Callable,
) -> None:
    """Run the orchestration pipeline and store results in session."""
    append_user_message(question)

    retriever = get_retriever()
    if not getattr(retriever, "loaded", False):
        append_assistant_message(
            "No index found. Please upload and process documents first."
        )
        return

    with st.spinner("Retrieving evidence and generating answer..."):
        orchestrator = get_orchestrator()
        result = orchestrator.process_query(question)
    set_selected_result(result)

    if result.is_abstained:
        content = (
            "I don't have sufficient evidence to answer this question.\n\n"
            f"**Reason:** {result.abstention_reason}"
        )
    elif result.answer in ("ERROR", "LLM_DISABLED"):
        if result.answer == "LLM_DISABLED":
            content = (
                "LLM is disabled (no API key configured). "
                "Showing retrieved evidence in the Audit Trace view."
            )
        else:
            content = "An error occurred during processing. Check server logs."
    else:
        content = result.answer

    append_assistant_message(content, result)


def _render_answer_footer(result: QueryResult, export_report_fn: Callable) -> None:
    """Render citation pills, confidence, status banners, and action buttons."""
    if result.citations:
        render_citation_pills(result.citations)

    if result.is_abstained:
        render_abstention_banner(result)

    if result.answer in ("ERROR", "LLM_DISABLED"):
        render_status_banner(result)
        return

    render_confidence_badge(result)
    render_status_banner(result)

    if result.critic_findings:
        n = len(result.critic_findings)
        suffix = "s" if n != 1 else ""
        st.markdown(
            badge_html(f"{n} critic flag{suffix}", "info"),
            unsafe_allow_html=True,
        )

    # Action bar
    col1, col2, col3 = st.columns(3)
    if col1.button(
        f'{ICONS["document"]} Audit Trace',
        key=f"audit_{result.query_id}",
        use_container_width=True,
    ):
        set_selected_result(result)
        switch_view("audit")
        st.rerun()
    if col2.button(
        f'{ICONS["search"]} Critic Lens',
        key=f"critic_{result.query_id}",
        use_container_width=True,
    ):
        set_selected_result(result)
        switch_view("critic")
        st.rerun()
    if col3.button(
        f'{ICONS["export"]} Export Report',
        key=f"export_{result.query_id}",
        use_container_width=True,
    ):
        export_report_fn(result)


# ================================================================== #
#  VIEW: Audit Trace                                                   #
# ================================================================== #

def render_audit_trace_view(export_report_fn: Callable) -> None:
    """Audit Trace mode — claim-by-claim verification dossier."""
    render_view_header("Audit Trace", "Claim-by-claim verification dossier with full evidence trail")

    result = get_selected_result()

    # Query selector from chat history
    messages = get_messages()
    assistant_results = [
        (i, m) for i, m in enumerate(messages)
        if m.get("role") == "assistant" and m.get("result") is not None
    ]

    if assistant_results:
        options = {
            f"Q{i+1}: {m['result'].question[:80]}": m["result"]
            for i, m in assistant_results
        }
        if options:
            selected_key = st.selectbox(
                "Select a query to audit",
                list(options.keys()),
                key="audit_select",
            )
            result = options[selected_key]
            set_selected_result(result)

    if result is None:
        render_empty_state(
            "No query selected",
            "Ask a question first, then return here to inspect the full audit trail.",
            "document",
        )
        return

    # Header card with question + answer
    answer_display = result.answer
    if len(answer_display) > 400:
        answer_display = answer_display[:400] + "..."

    st.markdown(
        f'<div class="pc-card">'
        f'<div style="font-size:0.78rem;color:{COLOURS["muted"]};text-transform:uppercase;'
        f'letter-spacing:0.04em;margin-bottom:0.3rem;">Query</div>'
        f'<div style="font-size:1rem;font-weight:600;color:{COLOURS["text"]};">'
        f'{result.question}</div>'
        f'<div style="margin-top:0.6rem;font-size:0.9rem;color:{COLOURS["text_secondary"]};">'
        f'{answer_display}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    render_status_banner(result)

    st.divider()

    # Two-column layout: claims (left), evidence rail (right)
    col_left, col_right = st.columns([7, 3])

    with col_left:
        render_confidence_badge(result)
        st.markdown("")

        section_header("Claim Verification")
        render_claim_verification_table(result)

        if result.contradictions:
            render_contradiction_section(result.contradictions)

        if result.critic_findings:
            section_header(f"Critic Findings ({len(result.critic_findings)})")
            render_critic_findings(result.critic_findings, filterable=False)

    with col_right:
        render_evidence_rail(result.evidence, highlight_pids=result.citations)

    st.divider()

    # Metadata and latency
    render_metadata_panel(result)
    render_latency_breakdown(result.latency)

    if result.notes:
        with st.expander("Pipeline Notes"):
            for note in result.notes:
                st.markdown(f"- `{note}`")

    # Export
    st.divider()
    section_header("Export Audit Report")
    export_report_fn(result)


# ================================================================== #
#  VIEW: Critic Lens                                                   #
# ================================================================== #

def render_critic_lens_view() -> None:
    """Critic Lens mode — policy language analysis (L1-L6)."""
    render_view_header(
        "Critic Lens",
        "Analyse policy text for normative language, unsupported claims, and logical fallacies (L1-L6)",
    )

    from policy_copilot.critic.critic_agent import detect_heuristic
    from policy_copilot.critic.labels import LABELS

    # Label reference as styled cards
    with st.expander("Label Reference (L1-L6)", expanded=False):
        for lid, info in LABELS.items():
            from policy_copilot.ui.theme import LABEL_COLOURS as LC
            lc = LC.get(lid, {"bg": "#f3f4f6", "text": "#6b7280"})
            st.markdown(
                f'<div style="padding:0.4rem 0.6rem;margin:0.2rem 0;border-radius:6px;'
                f'background:{lc["bg"]};font-size:0.88rem;">'
                f'<strong style="color:{lc["text"]};">{lid}: {info["name"]}</strong>'
                f' &mdash; {info["description"]}</div>',
                unsafe_allow_html=True,
            )

    tab_text, tab_evidence = st.tabs(["Analyse Text", "Analyse Evidence"])

    with tab_text:
        text_input = st.text_area(
            "Paste policy text to analyse",
            height=200,
            key="critic_text_input",
            placeholder="Paste a policy paragraph or section here to scan for normative language patterns...",
        )
        if st.button("Analyse", key="critic_analyse_btn", use_container_width=True) and text_input.strip():
            _run_critic_on_text(text_input, detect_heuristic, LABELS)

    with tab_evidence:
        result = get_selected_result()
        if result is None:
            render_empty_state(
                "No evidence loaded",
                "Ask a question first to populate evidence paragraphs for analysis.",
                "search",
            )
        else:
            st.markdown(
                f'<div class="pc-card">'
                f'<span style="font-size:0.78rem;color:{COLOURS["muted"]};">Analysing evidence from:</span><br>'
                f'<strong>{result.question[:80]}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

            findings = result.critic_findings
            if not findings:
                findings = _build_findings_from_evidence(result.evidence, detect_heuristic, LABELS)

            render_critic_findings(findings)

            if findings:
                st.divider()
                export_data = [f.model_dump() for f in findings]
                st.download_button(
                    f"{ICONS['export']} Export Critic Findings (JSON)",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"critic_findings_{result.query_id}.json",
                    mime="application/json",
                    use_container_width=True,
                )


def _run_critic_on_text(text: str, detect_fn: Callable, labels_ref: Dict) -> None:
    """Run critic analysis on arbitrary text and display results."""
    det = detect_fn(text)
    findings: List[CriticFinding] = []
    for label in det.get("labels", []):
        triggers = det.get("rationales", {}).get(label, [])
        findings.append(CriticFinding(
            label=label,
            label_name=labels_ref.get(label, {}).get("name", label),
            paragraph_id="(pasted text)",
            triggers=triggers if isinstance(triggers, list) else [str(triggers)],
            rationale=", ".join(triggers) if isinstance(triggers, list) else str(triggers),
            text_excerpt=text[:300],
        ))
    render_critic_findings(findings, filterable=True)


def _build_findings_from_evidence(
    evidence: List,
    detect_fn: Callable,
    labels_ref: Dict,
) -> List[CriticFinding]:
    """Build critic findings from evidence when none were pre-computed."""
    findings: List[CriticFinding] = []
    for ev in evidence:
        if not ev.text.strip():
            continue
        det = detect_fn(ev.text)
        for label in det.get("labels", []):
            triggers = det.get("rationales", {}).get(label, [])
            findings.append(CriticFinding(
                label=label,
                label_name=labels_ref.get(label, {}).get("name", label),
                paragraph_id=ev.paragraph_id,
                triggers=triggers if isinstance(triggers, list) else [str(triggers)],
                rationale=", ".join(triggers) if isinstance(triggers, list) else str(triggers),
                text_excerpt=ev.text[:300],
            ))
    return findings


# ================================================================== #
#  VIEW: Experiment Explorer                                           #
# ================================================================== #

def render_experiment_explorer_view() -> None:
    """Experiment Explorer mode — browse and compare evaluation runs."""
    render_view_header("Experiment Explorer", "Browse and compare evaluation runs")

    from policy_copilot.service.run_inspector import RunInspector

    inspector = RunInspector()
    runs = inspector.list_runs()

    if not runs:
        render_empty_state(
            "No evaluation runs found",
            "Run an evaluation with scripts/run_eval.py to populate results.",
            "chart",
        )
        return

    tab_browse, tab_compare = st.tabs(["Browse Runs", "Compare Runs"])

    with tab_browse:
        _render_run_browser(inspector, runs)

    with tab_compare:
        _render_run_comparison(inspector, runs)


def _render_run_browser(inspector: Any, runs: List) -> None:
    """Browse tab: single run detail with metrics and records."""
    run_names = [r.run_name for r in runs]
    selected = st.selectbox("Select a run", run_names, key="exp_run_select")

    detail = inspector.load_run(selected)
    if detail is None:
        st.warning("Could not load run.")
        return

    section_header("Summary Metrics")
    s = detail.summary

    mc = st.columns(4)
    mc[0].metric("Baseline", s.baseline.upper() if s.baseline else "N/A")
    mc[1].metric("Queries", s.total_queries)
    mc[2].metric(
        "Answer Rate",
        f"{s.answer_rate:.1%}" if s.answer_rate is not None else "N/A",
    )
    mc[3].metric(
        "Abstention Acc",
        f"{s.abstention_accuracy:.1%}" if s.abstention_accuracy is not None else "N/A",
    )

    mc2 = st.columns(4)
    mc2[0].metric(
        "Evidence Recall@5",
        f"{s.evidence_recall_at_5:.1%}" if s.evidence_recall_at_5 is not None else "N/A",
    )
    mc2[1].metric(
        "Citation Precision",
        f"{s.citation_precision:.1%}" if s.citation_precision is not None else "N/A",
    )
    mc2[2].metric("Provider", s.provider or "N/A")
    mc2[3].metric("Backend", s.backend_used or "N/A")

    with st.expander("Run Configuration"):
        st.json(detail.config)

    if detail.records:
        section_header(f"Per-Query Results ({len(detail.records)} queries)")
        for rec in detail.records:
            abstain_badge = badge_html("Abstained", "abstained") if rec.is_abstained else ""
            contra_badge = (
                badge_html(f"{len(rec.contradictions)} contradiction(s)", "contradiction")
                if rec.contradictions else ""
            )

            label = f"**{rec.query_id}** — {rec.question[:60]}"
            with st.expander(label):
                st.markdown(
                    f'<div style="margin-bottom:0.5rem;">'
                    f'{badge_html(rec.category, "info")} {abstain_badge} {contra_badge}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Answer:** {rec.answer[:300]}")
                if rec.citations:
                    from policy_copilot.ui.components import render_citation_pills as _pills
                    _pills(rec.citations)
                if rec.notes:
                    st.caption(f"Notes: {', '.join(rec.notes)}")
    else:
        render_empty_state("No per-query records", "This run has no outputs.jsonl data.", "document")


def _render_run_comparison(inspector: Any, runs: List) -> None:
    """Compare tab: side-by-side metric deltas."""
    section_header("Compare Two Runs")
    run_names = [r.run_name for r in runs]

    if len(run_names) < 2:
        render_empty_state("Need at least two runs", "Run more evaluations to enable comparison.", "compare")
        return

    col_a, col_b = st.columns(2)
    run_a = col_a.selectbox("Run A", run_names, index=0, key="cmp_a")
    run_b = col_b.selectbox("Run B", run_names, index=min(1, len(run_names) - 1), key="cmp_b")

    if run_a == run_b:
        st.warning("Select two different runs to compare.")
        return

    if st.button("Compare", use_container_width=True):
        comparison = inspector.compare_runs(run_a, run_b)
        if comparison is None:
            st.error("Could not load one or both runs.")
            return

        section_header("Metric Deltas (B - A)")
        for metric, delta in comparison.metric_deltas.items():
            if delta is not None:
                if delta > 0:
                    cls, prefix = "pc-delta-pos", "+"
                elif delta < 0:
                    cls, prefix = "pc-delta-neg", ""
                else:
                    cls, prefix = "pc-delta-zero", ""
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;'
                    f'border-bottom:1px solid {COLOURS["border"]};font-size:0.9rem;">'
                    f'<span>{metric}</span>'
                    f'<span class="{cls}">{prefix}{delta:.4f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;'
                    f'border-bottom:1px solid {COLOURS["border"]};font-size:0.9rem;color:{COLOURS["muted"]};">'
                    f'<span>{metric}</span><span>N/A</span></div>',
                    unsafe_allow_html=True,
                )

        if comparison.per_query:
            section_header(f"Per-Query Comparison ({len(comparison.per_query)} queries)")
            try:
                import pandas as pd
                df = pd.DataFrame(comparison.per_query)
                st.dataframe(df, use_container_width=True)
            except ImportError:
                st.json(comparison.per_query[:20])


# ================================================================== #
#  VIEW: Reviewer Mode                                                 #
# ================================================================== #

def render_reviewer_view() -> None:
    """Reviewer Mode — human rubric scoring of query results."""
    render_view_header("Reviewer Mode", "Human rubric scoring of query results")

    from policy_copilot.service.reviewer_service import (
        ReviewerService,
        ReviewSession,
    )
    from policy_copilot.service.run_inspector import RunInspector

    inspector = RunInspector()
    runs = inspector.list_runs()

    if not runs:
        render_empty_state(
            "No evaluation runs found",
            "Run an evaluation first to enable human review.",
            "pencil",
        )
        return

    run_names = [r.run_name for r in runs]
    selected_run = st.selectbox("Select run to review", run_names, key="rev_run")

    reviewer = ReviewerService()
    records = reviewer.load_queries_from_run(selected_run)
    if not records:
        render_empty_state(
            f"No query records for {selected_run}",
            "This run has no outputs.jsonl data to review.",
            "document",
        )
        return

    # Initialise review session in state
    sess_key = f"review_session_{selected_run}"
    if sess_key not in st.session_state:
        st.session_state[sess_key] = reviewer.create_session(selected_run)
    session: ReviewSession = st.session_state[sess_key]

    reviewed_count = len(session.reviews)
    total_count = len(records)
    render_progress_indicator(reviewed_count, total_count, "Review progress")

    st.divider()

    tab_score, tab_results = st.tabs(["Score Queries", "Review Summary"])

    with tab_score:
        _render_scoring_tab(records, session, reviewer)

    with tab_results:
        _render_review_summary(session, reviewer)


def _render_scoring_tab(
    records: List[Dict],
    session: Any,
    reviewer: Any,
) -> None:
    """Score Queries tab within Reviewer Mode."""
    from policy_copilot.service.reviewer_service import ReviewRubric

    query_labels = [
        f"{r.get('query_id', f'q{i}')}: {r.get('question', '')[:60]}"
        for i, r in enumerate(records)
    ]
    selected_idx = st.selectbox(
        "Select query",
        range(len(records)),
        format_func=lambda i: query_labels[i],
        key="rev_query",
    )
    rec = records[selected_idx]

    col_main, col_ev = st.columns([3, 2])

    with col_main:
        st.markdown(f"### {rec.get('question', 'N/A')}")

        is_abstained = rec.get("is_abstained", False)
        if is_abstained:
            st.markdown(
                f'<div class="pc-banner pc-banner--abstained">'
                f'<strong>System abstained.</strong> '
                f'Reason: {rec.get("abstention_reason", "N/A")}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**Answer:**\n\n{rec.get('answer', 'N/A')}")

        citations = rec.get("citations", [])
        if citations:
            render_citation_pills(citations)

        contras = rec.get("contradictions", [])
        if contras:
            st.markdown(
                f'{badge_html(f"{len(contras)} contradiction(s)", "contradiction")}',
                unsafe_allow_html=True,
            )
            for c in contras:
                if isinstance(c, dict):
                    from policy_copilot.service.schemas import ContradictionAlert
                    alert = ContradictionAlert(
                        paragraph_ids=c.get("paragraph_ids", []),
                        rationale=c.get("rationale", ""),
                        confidence=c.get("confidence", "low"),
                        text_a=c.get("text_a", ""),
                        text_b=c.get("text_b", ""),
                    )
                    render_contradiction_alert(alert)

    with col_ev:
        section_header("Retrieved Evidence")
        passages = rec.get("evidence", rec.get("passages", []))
        if passages:
            for i, p in enumerate(passages[:5], 1):
                pid = p.get("paragraph_id", p.get("id", f"p{i}"))
                text = p.get("text", "")[:300]
                with st.expander(f"{i}. `{pid}`", expanded=(i == 1)):
                    st.markdown(
                        f'<div class="pc-evidence-text">{text}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            render_empty_state("No evidence passages", icon="document")

    st.divider()

    # Rubric scoring form
    section_header("Rubric Scores")
    qid = rec.get("query_id", f"q{selected_idx}")
    already = [r for r in session.reviews if r.query_id == qid]
    if already:
        last = already[-1]
        st.success(
            f"Already reviewed (G={last.groundedness} / U={last.usefulness} "
            f"/ C={last.citation_correctness}). Submit again to update."
        )

    with st.form(key=f"rubric_form_{qid}"):
        c1, c2, c3 = st.columns(3)
        groundedness = c1.slider(
            "Groundedness", 1, 5, 3,
            help="Is the answer fully supported by the cited evidence?",
        )
        usefulness = c2.slider(
            "Usefulness", 1, 5, 3,
            help="Does the answer effectively address the question?",
        )
        citation_corr = c3.slider(
            "Citation Correctness", 1, 5, 3,
            help="Are the citations accurate and relevant?",
        )
        notes = st.text_input("Notes (optional)", key=f"rev_notes_{qid}")

        submitted = st.form_submit_button("Submit Review", use_container_width=True)
        if submitted:
            review = ReviewRubric(
                query_id=qid,
                question=rec.get("question", ""),
                groundedness=groundedness,
                usefulness=usefulness,
                citation_correctness=citation_corr,
                notes=notes,
            )
            reviewer.add_review(session, review)
            st.success(f"Review saved for {qid}")
            st.rerun()


def _render_review_summary(session: Any, reviewer: Any) -> None:
    """Review Summary tab within Reviewer Mode."""
    if not session.reviews:
        render_empty_state(
            "No reviews submitted yet",
            "Score some queries in the Score tab first.",
            "pencil",
        )
        return

    stats = reviewer.summary_stats(session)
    section_header("Summary Statistics")
    sc = st.columns(4)
    sc[0].metric("Reviews", stats.get("total_reviews", 0))
    sc[1].metric("Groundedness (mean)", stats.get("groundedness_mean", "N/A"))
    sc[2].metric("Usefulness (mean)", stats.get("usefulness_mean", "N/A"))
    sc[3].metric("Citation (mean)", stats.get("citation_correctness_mean", "N/A"))

    st.divider()

    section_header("All Reviews")
    try:
        import pandas as pd
        rows = [r.model_dump() for r in session.reviews]
        df = pd.DataFrame(rows)
        display_cols = ["query_id", "groundedness", "usefulness",
                        "citation_correctness", "notes", "timestamp"]
        st.dataframe(
            df[[c for c in display_cols if c in df.columns]],
            use_container_width=True,
        )
    except ImportError:
        for r in session.reviews:
            st.text(f"{r.query_id}: G={r.groundedness} U={r.usefulness} C={r.citation_correctness}")

    st.divider()

    section_header("Export Reviews")
    ecol1, ecol2 = st.columns(2)
    ecol1.download_button(
        f"{ICONS['export']} Download JSON",
        data=reviewer.export_json(session),
        file_name=f"review_session_{session.session_id}.json",
        mime="application/json",
        use_container_width=True,
    )
    ecol2.download_button(
        f"{ICONS['export']} Download CSV",
        data=reviewer.export_csv(session),
        file_name=f"review_session_{session.session_id}.csv",
        mime="text/csv",
        use_container_width=True,
    )
