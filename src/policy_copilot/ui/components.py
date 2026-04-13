"""
Reusable Streamlit rendering components.

Each function renders a self-contained UI fragment.  No component
accesses the service layer or session state directly — all data is
passed in as arguments.  All visual constants come from ``theme.py``.
"""
from __future__ import annotations

from typing import Any, List, Optional

import streamlit as st

from policy_copilot.service.schemas import (
    ClaimDetail,
    ContradictionAlert,
    CriticFinding,
    EvidenceItem,
    LatencyBreakdown,
    QueryResult,
)
from policy_copilot.ui.theme import (
    COLOURS,
    ICONS,
    LABEL_COLOURS,
    badge_html,
    render_empty_state,
    section_header,
)

# ------------------------------------------------------------------ #
#  Chat                                                                #
# ------------------------------------------------------------------ #

SAMPLE_PROMPTS = [
    ("What is the university's policy on academic integrity?", "document"),
    ("What are the requirements for submitting coursework extensions?", "clock"),
    ("How does the grievance procedure work?", "shield"),
    ("What accessibility support is available for students?", "search"),
]


def render_sample_prompts() -> Optional[str]:
    """Show clickable sample prompt chips in a 2x2 grid.  Returns the selected prompt or None."""
    cols = st.columns(2)
    for i, (prompt, icon_key) in enumerate(SAMPLE_PROMPTS):
        icon_char = ICONS.get(icon_key, "")
        col = cols[i % 2]
        if col.button(
            f"{icon_char}  {prompt}",
            key=f"sample_{hash(prompt)}",
            use_container_width=True,
        ):
            return prompt
    return None


def render_chat_empty_state() -> Optional[str]:
    """Branded welcome hero with capabilities and sample prompts."""
    st.markdown(
        '<div class="pc-hero">'
        "<h2>Policy Copilot</h2>"
        '<p class="pc-hero-tagline">'
        "Audit-ready answers grounded in policy evidence. "
        "Every answer comes with its receipts.</p>"
        '<div class="pc-hero-capabilities">'
        f'<div class="pc-hero-cap-item"><span class="pc-hero-cap-icon">{ICONS["check"]}</span> Evidence-grounded answers with paragraph-level citations</div>'
        f'<div class="pc-hero-cap-item"><span class="pc-hero-cap-icon">{ICONS["warning"]}</span> Abstains when evidence is insufficient</div>'
        f'<div class="pc-hero-cap-item"><span class="pc-hero-cap-icon">{ICONS["shield"]}</span> Detects contradictions between policy sources</div>'
        f'<div class="pc-hero-cap-item"><span class="pc-hero-cap-icon">{ICONS["export"]}</span> Exportable audit reports in JSON, HTML, and Markdown</div>'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    section_header("Try a question")
    return render_sample_prompts()


# ------------------------------------------------------------------ #
#  Evidence                                                            #
# ------------------------------------------------------------------ #

def render_evidence_card(
    ev: EvidenceItem,
    index: int = 0,
    expanded: bool = False,
    highlight_pids: Optional[List[str]] = None,
) -> None:
    """Expandable card for a single evidence paragraph."""
    is_highlight = highlight_pids and ev.paragraph_id in highlight_pids
    border_style = f"border-left:3px solid {COLOURS['primary']};" if is_highlight else ""

    score_parts = [f"retrieve={ev.score_retrieve:.4f}", f"rerank={ev.score_rerank:.4f}"]
    if ev.fused_score is not None:
        score_parts.append(f"fused={ev.fused_score:.6f}")
    score_str = "  ".join(score_parts)

    doc_type_pill = ""
    if ev.doc_type and ev.doc_type != "policy document":
        doc_type_pill = f" [{ev.doc_type}]"
    cited_badge = ""
    if is_highlight:
        cited_badge = ' <span class="pc-badge" style="background:#dcfce7;color:#166534;font-size:0.7rem;">Cited</span>'
    label = f"**{index}.** `{ev.paragraph_id}` — {ev.source_file} p.{ev.page}{doc_type_pill}{cited_badge}"

    with st.expander(label, expanded=expanded):
        meta_parts = [f'<span class="pc-evidence-score">{score_str}</span>']
        if ev.dense_rank is not None or ev.sparse_rank is not None:
            meta_parts.append(
                f'<span class="pc-evidence-meta"> dense_rank={ev.dense_rank}  sparse_rank={ev.sparse_rank}</span>'
            )
        st.markdown(" ".join(meta_parts), unsafe_allow_html=True)

        text = ev.text[:600] if ev.text else "_No text available_"
        st.markdown(
            f'<div class="pc-evidence-text" style="{border_style}">{text}</div>',
            unsafe_allow_html=True,
        )
        cite_str = f"{ev.source_file}, p.{ev.page}, §{ev.paragraph_id}"
        st.code(cite_str, language=None)


def render_evidence_rail(
    evidence: List[EvidenceItem],
    highlight_pids: Optional[List[str]] = None,
) -> None:
    """Render all evidence items as a vertical rail with header."""
    st.markdown(
        f'<p class="pc-evidence-header">'
        f'{ICONS["document"]} Evidence ({len(evidence)} paragraphs)</p>',
        unsafe_allow_html=True,
    )
    if not evidence:
        render_empty_state("No evidence available", "Run a query to populate evidence.", "search")
        return
    for i, ev in enumerate(evidence, 1):
        render_evidence_card(ev, i, expanded=(i == 1), highlight_pids=highlight_pids)


def render_citation_pills(citations: List[str]) -> None:
    """Render inline citation pills."""
    if not citations:
        return
    pills_html = " ".join(
        f'<span class="pc-citation-pill">{pid}</span>'
        for pid in citations
    )
    st.markdown(pills_html, unsafe_allow_html=True)


# ------------------------------------------------------------------ #
#  Confidence / Abstention / Contradictions                            #
# ------------------------------------------------------------------ #

def render_confidence_badge(result: QueryResult) -> None:
    """Visual confidence indicator using design-system badges."""
    max_r = result.confidence_max_rerank
    threshold = result.abstain_threshold
    if max_r >= threshold * 2:
        variant, label = "high", "HIGH"
    elif max_r >= threshold:
        variant, label = "moderate", "MODERATE"
    else:
        variant, label = "low", "LOW"

    st.markdown(
        f'{badge_html(f"Confidence: {label} ({max_r:.4f})", variant)}',
        unsafe_allow_html=True,
    )


def render_abstention_banner(result: QueryResult) -> None:
    """Structured warning panel when the system abstains."""
    reason = result.abstention_reason or "Insufficient evidence confidence"
    st.markdown(
        f'<div class="pc-abstention-panel">'
        f'<h4>{ICONS["warning"]} Insufficient Evidence — System Abstained</h4>'
        f'<div class="pc-abstention-details">'
        f'<strong>Why:</strong> {reason}<br>'
        f'<strong>Confidence:</strong> Max rerank score = {result.confidence_max_rerank:.4f} '
        f'(threshold = {result.abstain_threshold:.2f})'
        f'</div>'
        f'<div class="pc-abstention-guidance">'
        f'<strong>What would help?</strong> '
        f'Try rephrasing your question with more specific terms from the policy documents, '
        f'or check whether the topic is covered in the indexed corpus. '
        f'The evidence rail below shows what was retrieved — review it to '
        f'see if relevant content was found but scored below threshold.'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_status_banner(result: QueryResult) -> None:
    """Auto-select and render the appropriate status banner for a result."""
    if result.is_abstained:
        render_abstention_banner(result)
        return

    if result.answer in ("ERROR",):
        st.markdown(
            f'<div class="pc-banner pc-banner--error">'
            f'<strong>{ICONS["cross"]} Processing Error</strong><br>'
            f'An error occurred during pipeline execution. Check server logs.'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    if result.answer == "LLM_DISABLED":
        st.markdown(
            f'<div class="pc-banner pc-banner--fallback">'
            f'<strong>{ICONS["warning"]} LLM Disabled</strong><br>'
            f'No API key configured. Showing retrieved evidence only.'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    if result.contradictions:
        n = len(result.contradictions)
        st.markdown(
            f'<div class="pc-banner pc-banner--contradiction">'
            f'<strong>{ICONS["warning"]} {n} Contradiction{"s" if n != 1 else ""} Detected</strong><br>'
            f'Conflicting information was found in the retrieved evidence. '
            f'Review the Audit Trace for details.'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_contradiction_alert(contradiction: ContradictionAlert) -> None:
    """Side-by-side contradiction display using the design system."""
    pid_a = contradiction.paragraph_ids[0] if contradiction.paragraph_ids else "?"
    pid_b = contradiction.paragraph_ids[1] if len(contradiction.paragraph_ids) > 1 else "?"
    text_a = contradiction.text_a[:400] if contradiction.text_a else "N/A"
    text_b = contradiction.text_b[:400] if contradiction.text_b else "N/A"

    conf_badge = badge_html(contradiction.confidence.upper(), "danger")

    st.markdown(
        f'<div class="pc-card pc-card--contradiction">'
        f'<strong>{ICONS["warning"]} Contradiction</strong> '
        f'{conf_badge} '
        f'<span style="font-size:0.82rem;color:{COLOURS["muted"]};">Tier {contradiction.tier}</span>'
        f'<p style="font-size:0.85rem;color:{COLOURS["text_secondary"]};margin:0.3rem 0;">'
        f'{contradiction.rationale}</p>'
        f'<div class="pc-contra-grid">'
        f'<div class="pc-contra-side"><div class="pc-contra-pid">{pid_a}</div>{text_a}</div>'
        f'<div class="pc-contra-side"><div class="pc-contra-pid">{pid_b}</div>{text_b}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def render_contradiction_section(contradictions: List[ContradictionAlert]) -> None:
    """Render all contradictions with a styled header."""
    if not contradictions:
        return
    section_header(f"Contradictions ({len(contradictions)})")
    for c in contradictions:
        render_contradiction_alert(c)


# ------------------------------------------------------------------ #
#  Claim verification                                                  #
# ------------------------------------------------------------------ #

def render_claim_row(claim: ClaimDetail) -> None:
    """Single claim with support status, styled as a card."""
    variant = "claim-supported" if claim.supported else "claim-unsupported"
    status_badge = badge_html("Supported", "supported") if claim.supported else badge_html("Unsupported", "unsupported")

    cite_html = ""
    if claim.citations:
        cite_html = " ".join(
            f'<span class="pc-citation-pill">{c}</span>' for c in claim.citations
        )

    st.markdown(
        f'<div class="pc-card pc-card--{variant}">'
        f'<div class="pc-claim-text">'
        f'<strong>Claim {claim.claim_id}:</strong> {claim.text}'
        f'</div>'
        f'<div class="pc-claim-meta">'
        f'{status_badge} '
        f'<span style="margin-left:0.5rem;font-size:0.8rem;color:{COLOURS["muted"]};">'
        f'{claim.support_rationale}</span>'
        f'</div>'
        f'{f"<div style=&quot;margin-top:0.3rem;&quot;>{cite_html}</div>" if cite_html else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if claim.evidence_excerpt:
        with st.expander("Evidence excerpt", expanded=False):
            st.markdown(
                f'<div class="pc-evidence-text">{claim.evidence_excerpt}</div>',
                unsafe_allow_html=True,
            )


def _support_rate_bar(rate: float) -> str:
    """Return HTML for a support-rate progress bar."""
    pct = max(0, min(100, int(rate * 100)))
    if pct >= 80:
        fill_cls = "pc-progress-fill--success"
    elif pct >= 50:
        fill_cls = "pc-progress-fill--warning"
    else:
        fill_cls = "pc-progress-fill--danger"
    return (
        f'<div class="pc-progress-container">'
        f'<div class="pc-progress-fill {fill_cls}" style="width:{pct}%;"></div>'
        f'</div>'
    )


def render_claim_verification_table(result: QueryResult) -> None:
    """Full claim-by-claim breakdown with progress bar."""
    cv = result.claim_verification
    if cv is None:
        render_empty_state("No claim verification data", "The pipeline did not produce claim-level analysis.", "document")
        return

    total = cv.supported_claims + cv.unsupported_claims
    st.markdown(
        f'<div style="margin-bottom:0.75rem;">'
        f'<strong>Support rate:</strong> {cv.support_rate:.0%} '
        f'({cv.supported_claims} of {total} claims supported)'
        f'{_support_rate_bar(cv.support_rate)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    for claim in cv.claims:
        render_claim_row(claim)


# ------------------------------------------------------------------ #
#  Critic                                                              #
# ------------------------------------------------------------------ #

def render_critic_flag(finding: CriticFinding) -> None:
    """Single critic flag card with category colouring."""
    lc = LABEL_COLOURS.get(finding.label, {"bg": COLOURS["muted_light"], "text": COLOURS["muted"]})
    triggers_str = ", ".join(finding.triggers) if finding.triggers else "N/A"
    excerpt = finding.text_excerpt[:200] if finding.text_excerpt else ""

    st.markdown(
        f'<div class="pc-critic-card" style="background:{lc["bg"]};">'
        f'<span class="pc-critic-label" style="color:{lc["text"]};">'
        f'[{finding.label}] {finding.label_name}</span> '
        f'{badge_html(finding.paragraph_id, "info")}'
        f'<div class="pc-critic-triggers"><strong>Triggers:</strong> {triggers_str}</div>'
        f'{f"<div class=&quot;pc-critic-excerpt&quot;>&quot;{excerpt}&quot;</div>" if excerpt else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_critic_findings(
    findings: List[CriticFinding],
    filterable: bool = True,
) -> None:
    """Render critic findings grouped by label, with optional filter."""
    if not findings:
        render_empty_state("No critic findings", "No policy language issues detected.", "check")
        return

    labels_present = sorted({f.label for f in findings})

    # Count badges at the top
    count_parts = []
    for lab in labels_present:
        n = sum(1 for f in findings if f.label == lab)
        lc = LABEL_COLOURS.get(lab, {"bg": COLOURS["muted_light"], "text": COLOURS["muted"]})
        count_parts.append(
            f'<span class="pc-badge" style="background:{lc["bg"]};color:{lc["text"]};">'
            f'{lab}: {n}</span>'
        )
    st.markdown(
        f'<div style="margin-bottom:0.5rem;">'
        f'<strong>{len(findings)} finding{"s" if len(findings) != 1 else ""}</strong> '
        f'{" ".join(count_parts)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if filterable and len(labels_present) > 1:
        selected = st.multiselect(
            "Filter by label",
            labels_present,
            default=labels_present,
            key="critic_filter",
        )
        findings = [f for f in findings if f.label in selected]

    for f in findings:
        render_critic_flag(f)


# ------------------------------------------------------------------ #
#  Metrics / metadata                                                  #
# ------------------------------------------------------------------ #

def render_metric_card(label: str, value: Any, delta: Optional[str] = None) -> None:
    """KPI-style metric display using the design-system card."""
    delta_html = ""
    if delta is not None:
        cls = "pc-delta-pos" if delta.startswith("+") else "pc-delta-neg" if delta.startswith("-") else "pc-delta-zero"
        delta_html = f'<div class="pc-metric-delta {cls}">{delta}</div>'
    st.markdown(
        f'<div class="pc-card pc-card--metric">'
        f'<div class="pc-metric-label">{label}</div>'
        f'<div class="pc-metric-value">{value}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_latency_breakdown(latency: LatencyBreakdown) -> None:
    """Horizontal bar visualisation of per-stage latency."""
    section_header("Latency Breakdown")

    stages = [
        ("Retrieval", latency.retrieval_ms),
        ("Reranking", latency.rerank_ms),
        ("LLM Generation", latency.llm_gen_ms),
        ("Verification", latency.verify_ms),
        ("Contradictions", latency.contradictions_ms),
        ("Critic", latency.critic_ms),
    ]
    max_ms = max((ms for _, ms in stages), default=1) or 1

    for stage_name, ms in stages:
        bar_pct = max(1, int((ms / max_ms) * 100))
        st.markdown(
            f'<div class="pc-latency-bar-container">'
            f'<span class="pc-latency-label">{stage_name}</span>'
            f'<div style="flex:1;background:#e2e8f0;border-radius:4px;height:8px;">'
            f'<div class="pc-latency-bar" style="width:{bar_pct}%;"></div>'
            f'</div>'
            f'<span class="pc-latency-value">{ms:.0f} ms</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="text-align:right;font-size:0.85rem;font-weight:600;'
        f'color:{COLOURS["text"]};margin-top:0.3rem;">'
        f'Total: {latency.total_ms:.0f} ms</div>',
        unsafe_allow_html=True,
    )


def render_metadata_panel(result: QueryResult) -> None:
    """Provider / backend / config metadata in a clean grid."""
    section_header("Pipeline Metadata")

    items = [
        ("Provider", result.provider or "N/A"),
        ("Model", result.model or "N/A"),
        ("Backend Requested", result.backend_requested),
        ("Backend Used", result.backend_used),
        ("Fusion Method", result.fusion_method or "N/A"),
        ("Total Latency", f"{result.latency.total_ms:.0f} ms"),
    ]

    cells = "".join(
        f'<div class="pc-meta-item">'
        f'<div class="pc-meta-key">{key}</div>'
        f'<div class="pc-meta-value">{val}</div>'
        f'</div>'
        for key, val in items
    )

    st.markdown(f'<div class="pc-meta-grid">{cells}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ #
#  Status / feedback helpers                                           #
# ------------------------------------------------------------------ #

def render_export_feedback(success: bool, filename: str = "") -> None:
    """Toast-like feedback after an export operation."""
    if success:
        st.success(f"Export complete: {filename}" if filename else "Export complete")
    else:
        st.error("Export failed. Check server logs.")


def render_progress_indicator(current: int, total: int, label: str = "Progress") -> None:
    """Render a progress indicator with count and bar."""
    if total <= 0:
        return
    pct = max(0, min(100, int((current / total) * 100)))
    st.markdown(
        f'<div style="margin-bottom:0.5rem;">'
        f'<span style="font-size:0.85rem;font-weight:600;color:{COLOURS["text_secondary"]};">'
        f'{label}: {current} of {total}</span>'
        f'<div class="pc-progress-container">'
        f'<div class="pc-progress-fill pc-progress-fill--primary" style="width:{pct}%;"></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ #
#  View header helper                                                  #
# ------------------------------------------------------------------ #

def render_view_header(title: str, subtitle: str = "") -> None:
    """Render the standard view header with title and subtitle."""
    st.markdown(f'<p class="pc-view-header">{title}</p>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="pc-view-subtitle">{subtitle}</p>', unsafe_allow_html=True)
