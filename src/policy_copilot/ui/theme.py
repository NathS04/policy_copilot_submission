"""
Centralised design system for the Policy Copilot UI.

Provides colour tokens, CSS injection, status badges, empty states,
and reusable HTML helpers.  Every visual constant lives here so that
components.py and renderers.py never hard-code colours or styles.
"""
from __future__ import annotations

import streamlit as st

# ------------------------------------------------------------------ #
#  Colour palette                                                      #
# ------------------------------------------------------------------ #

COLOURS = {
    "primary":       "#2563eb",
    "primary_light": "#dbeafe",
    "primary_dark":  "#1e40af",
    "success":       "#16a34a",
    "success_light": "#dcfce7",
    "success_dark":  "#166534",
    "warning":       "#d97706",
    "warning_light": "#fef3c7",
    "warning_dark":  "#92400e",
    "danger":        "#dc2626",
    "danger_light":  "#fef2f2",
    "danger_dark":   "#991b1b",
    "info":          "#0891b2",
    "info_light":    "#cffafe",
    "info_dark":     "#155e75",
    "muted":         "#6b7280",
    "muted_light":   "#f3f4f6",
    "surface":       "#ffffff",
    "background":    "#f8fafc",
    "border":        "#e2e8f0",
    "border_strong": "#cbd5e1",
    "text":          "#1e293b",
    "text_secondary": "#475569",
}

LABEL_COLOURS = {
    "L1": {"bg": "#fecaca", "text": "#991b1b"},
    "L2": {"bg": "#fed7aa", "text": "#9a3412"},
    "L3": {"bg": "#fef08a", "text": "#854d0e"},
    "L4": {"bg": "#bbf7d0", "text": "#166534"},
    "L5": {"bg": "#bfdbfe", "text": "#1e40af"},
    "L6": {"bg": "#e9d5ff", "text": "#6b21a8"},
}

# ------------------------------------------------------------------ #
#  Icon map (text-only, no emoji)                                      #
# ------------------------------------------------------------------ #

ICONS = {
    "check":         "&#10003;",
    "cross":         "&#10007;",
    "warning":       "&#9888;",
    "shield":        "&#9733;",
    "search":        "&#8981;",
    "document":      "&#9776;",
    "arrow_right":   "&#8594;",
    "clock":         "&#9201;",
    "export":        "&#8615;",
    "copy":          "&#9112;",
    "compare":       "&#8646;",
    "filter":        "&#9682;",
    "chart":         "&#9636;",
    "pencil":        "&#9998;",
}

# ------------------------------------------------------------------ #
#  Status badge variants                                               #
# ------------------------------------------------------------------ #

_BADGE_VARIANTS = {
    "supported":     {"bg": COLOURS["success_light"], "fg": COLOURS["success_dark"],  "label": "Supported"},
    "unsupported":   {"bg": COLOURS["danger_light"],  "fg": COLOURS["danger_dark"],   "label": "Unsupported"},
    "abstained":     {"bg": COLOURS["warning_light"], "fg": COLOURS["warning_dark"],  "label": "Abstained"},
    "contradiction": {"bg": COLOURS["danger_light"],  "fg": COLOURS["danger"],        "label": "Contradiction"},
    "fallback":      {"bg": COLOURS["warning_light"], "fg": COLOURS["warning_dark"],  "label": "Fallback"},
    "answerable":    {"bg": COLOURS["success_light"], "fg": COLOURS["success_dark"],  "label": "Answerable"},
    "unanswerable":  {"bg": COLOURS["muted_light"],   "fg": COLOURS["muted"],         "label": "Unanswerable"},
    "high":          {"bg": COLOURS["success_light"], "fg": COLOURS["success_dark"],  "label": "High"},
    "moderate":      {"bg": COLOURS["warning_light"], "fg": COLOURS["warning_dark"],  "label": "Moderate"},
    "low":           {"bg": COLOURS["danger_light"],  "fg": COLOURS["danger_dark"],   "label": "Low"},
    "info":          {"bg": COLOURS["info_light"],    "fg": COLOURS["info_dark"],     "label": "Info"},
    "saved":         {"bg": COLOURS["success_light"], "fg": COLOURS["success_dark"],  "label": "Saved"},
    "exported":      {"bg": COLOURS["primary_light"], "fg": COLOURS["primary_dark"],  "label": "Exported"},
    "error":         {"bg": COLOURS["danger_light"],  "fg": COLOURS["danger_dark"],   "label": "Error"},
}


def badge_html(label: str, variant: str = "info") -> str:
    """Return an inline HTML badge string for the given variant."""
    spec = _BADGE_VARIANTS.get(variant, _BADGE_VARIANTS["info"])
    return (
        f'<span class="pc-badge" style="background:{spec["bg"]};'
        f'color:{spec["fg"]};">{label}</span>'
    )


def render_status_badge(label: str, variant: str = "info") -> None:
    """Render an inline status badge via st.markdown."""
    st.markdown(badge_html(label, variant), unsafe_allow_html=True)


# ------------------------------------------------------------------ #
#  Empty state                                                         #
# ------------------------------------------------------------------ #

def render_empty_state(
    title: str,
    description: str = "",
    icon: str = "search",
) -> None:
    """Render a professional empty-state placeholder."""
    icon_char = ICONS.get(icon, ICONS["search"])
    desc_html = f'<p class="pc-empty-desc">{description}</p>' if description else ""
    st.markdown(
        f'<div class="pc-empty-state">'
        f'<div class="pc-empty-icon">{icon_char}</div>'
        f'<p class="pc-empty-title">{title}</p>'
        f'{desc_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------ #
#  Section header helper                                               #
# ------------------------------------------------------------------ #

def section_header(title: str, subtitle: str = "") -> None:
    """Render a styled section header with optional subtitle."""
    st.markdown(
        f'<h3 class="pc-section-header">{title}</h3>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.caption(subtitle)


# ------------------------------------------------------------------ #
#  Card wrapper                                                        #
# ------------------------------------------------------------------ #

def card_html(content: str, variant: str = "") -> str:
    """Wrap content in a styled card div.  Variant adds a modifier class."""
    cls = f"pc-card pc-card--{variant}" if variant else "pc-card"
    return f'<div class="{cls}">{content}</div>'


def render_card(content: str, variant: str = "") -> None:
    """Render a card via st.markdown."""
    st.markdown(card_html(content, variant), unsafe_allow_html=True)


# ------------------------------------------------------------------ #
#  Master CSS injection                                                #
# ------------------------------------------------------------------ #

def inject_global_css() -> None:
    """Inject the full design-system stylesheet. Call once from the app shell."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


_GLOBAL_CSS = """<style>
/* ============================================================
   Policy Copilot — Design System CSS
   ============================================================ */

/* --- Base & Layout ------------------------------------------ */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}
[data-testid="stSidebar"] {
    min-width: 270px;
    max-width: 310px;
    background: #f1f5f9;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.92rem;
}

/* --- Sidebar branding --------------------------------------- */
.pc-sidebar-brand {
    padding: 0.25rem 0 0.5rem 0;
}
.pc-sidebar-brand h2 {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0 0 0.1rem 0;
    color: #1e293b;
    letter-spacing: -0.01em;
}
.pc-sidebar-brand p {
    font-size: 0.8rem;
    color: #64748b;
    margin: 0;
}
.pc-sidebar-divider {
    border: none;
    border-top: 1px solid #cbd5e1;
    margin: 0.7rem 0;
}

/* --- View header -------------------------------------------- */
.pc-view-header {
    font-size: 1.45rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.15rem 0;
    letter-spacing: -0.01em;
}
.pc-view-subtitle {
    font-size: 0.88rem;
    color: #64748b;
    margin: 0 0 1rem 0;
}

/* --- Section headers ---------------------------------------- */
.pc-section-header {
    font-size: 1.05rem;
    font-weight: 650;
    color: #334155;
    margin: 1.4rem 0 0.35rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #e2e8f0;
}

/* --- Cards -------------------------------------------------- */
.pc-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.75rem;
    line-height: 1.55;
}
.pc-card--evidence {
    border-left: 3px solid #2563eb;
}
.pc-card--claim-supported {
    border-left: 3px solid #16a34a;
}
.pc-card--claim-unsupported {
    border-left: 3px solid #dc2626;
}
.pc-card--contradiction {
    border-left: 3px solid #dc2626;
    background: #fef2f2;
}
.pc-card--abstention {
    border-left: 3px solid #d97706;
    background: #fffbeb;
}
.pc-card--fallback {
    border-left: 3px solid #d97706;
    background: #fef3c7;
}
.pc-card--welcome {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
    border: 1px solid #c7d2fe;
    text-align: center;
    padding: 2rem 1.5rem;
}
.pc-card--metric {
    text-align: center;
    padding: 0.85rem 0.75rem;
}
.pc-card--metric .pc-metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0.2rem 0;
}
.pc-card--metric .pc-metric-label {
    font-size: 0.78rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.pc-card--metric .pc-metric-delta {
    font-size: 0.82rem;
    font-weight: 600;
}

/* --- Badges ------------------------------------------------- */
.pc-badge {
    display: inline-block;
    padding: 2px 10px;
    margin: 2px 3px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1.6;
    vertical-align: middle;
}

/* --- Citation pills ----------------------------------------- */
.pc-citation-pill {
    display: inline-block;
    padding: 1px 9px;
    margin: 2px 2px;
    border-radius: 10px;
    background: #dbeafe;
    color: #1e40af;
    font-size: 0.76rem;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-weight: 500;
    letter-spacing: 0.01em;
    vertical-align: middle;
}

/* --- Evidence rail ------------------------------------------ */
.pc-evidence-header {
    font-size: 0.95rem;
    font-weight: 650;
    color: #334155;
    margin: 0 0 0.6rem 0;
}
.pc-evidence-score {
    font-size: 0.75rem;
    color: #64748b;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
.pc-evidence-text {
    font-size: 0.84rem;
    color: #475569;
    line-height: 1.55;
    margin-top: 0.35rem;
}
.pc-evidence-pid {
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    color: #1e40af;
}
.pc-evidence-meta {
    font-size: 0.75rem;
    color: #94a3b8;
}

/* --- Status banners ----------------------------------------- */
.pc-banner {
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.75rem;
    font-size: 0.9rem;
    line-height: 1.5;
}
.pc-banner--supported {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #bbf7d0;
}
.pc-banner--abstained {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
}
.pc-banner--contradiction {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
}
.pc-banner--fallback {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
}
.pc-banner--error {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
}

/* --- Action bar --------------------------------------------- */
.pc-action-bar {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.6rem;
    flex-wrap: wrap;
}

/* --- Claim rows --------------------------------------------- */
.pc-claim-card {
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    background: #ffffff;
}
.pc-claim-card--supported {
    border-left: 3px solid #16a34a;
}
.pc-claim-card--unsupported {
    border-left: 3px solid #dc2626;
}
.pc-claim-text {
    font-size: 0.9rem;
    color: #334155;
    line-height: 1.5;
}
.pc-claim-meta {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 0.3rem;
}

/* --- Critic flags ------------------------------------------- */
.pc-critic-card {
    padding: 0.7rem 1rem;
    margin: 0.35rem 0;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}
.pc-critic-label {
    font-weight: 700;
    font-size: 0.88rem;
}
.pc-critic-triggers {
    font-size: 0.82rem;
    color: #475569;
    margin-top: 0.2rem;
}
.pc-critic-excerpt {
    font-size: 0.8rem;
    color: #94a3b8;
    font-style: italic;
    margin-top: 0.25rem;
    line-height: 1.45;
}

/* --- Progress bar ------------------------------------------- */
.pc-progress-container {
    background: #e2e8f0;
    border-radius: 6px;
    height: 10px;
    width: 100%;
    margin: 0.4rem 0;
    overflow: hidden;
}
.pc-progress-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.3s ease;
}
.pc-progress-fill--success { background: #16a34a; }
.pc-progress-fill--warning { background: #d97706; }
.pc-progress-fill--danger  { background: #dc2626; }
.pc-progress-fill--primary { background: #2563eb; }

/* --- Metric cards (Streamlit native override) --------------- */
div[data-testid="stMetric"] {
    background: #ffffff;
    padding: 14px 16px;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

/* --- Chat messages ------------------------------------------ */
.stChatMessage {
    max-width: 100%;
}
div[data-testid="stChatMessage"] {
    line-height: 1.6;
}

/* --- Empty state -------------------------------------------- */
.pc-empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #94a3b8;
}
.pc-empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    opacity: 0.6;
}
.pc-empty-title {
    font-size: 1rem;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 0.25rem;
}
.pc-empty-desc {
    font-size: 0.85rem;
    color: #94a3b8;
}

/* --- Sample prompt chips ------------------------------------ */
.pc-prompt-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    margin: 1rem 0;
}
.pc-prompt-chip {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 0.87rem;
    color: #334155;
    line-height: 1.45;
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.pc-prompt-chip:hover {
    border-color: #2563eb;
    box-shadow: 0 0 0 1px #2563eb;
}

/* --- Latency bar -------------------------------------------- */
.pc-latency-bar-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.25rem 0;
}
.pc-latency-label {
    font-size: 0.82rem;
    color: #475569;
    min-width: 110px;
}
.pc-latency-bar {
    height: 8px;
    border-radius: 4px;
    background: #2563eb;
    transition: width 0.3s;
}
.pc-latency-value {
    font-size: 0.78rem;
    color: #64748b;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    min-width: 60px;
}

/* --- Metadata grid ------------------------------------------ */
.pc-meta-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
}
.pc-meta-item {
    padding: 0.6rem 0.75rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}
.pc-meta-key {
    font-size: 0.72rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.15rem;
}
.pc-meta-value {
    font-size: 0.88rem;
    color: #1e293b;
    font-weight: 500;
}

/* --- Comparison delta --------------------------------------- */
.pc-delta-pos { color: #16a34a; font-weight: 600; }
.pc-delta-neg { color: #dc2626; font-weight: 600; }
.pc-delta-zero { color: #64748b; }

/* --- Contradiction side-by-side ----------------------------- */
.pc-contra-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin-top: 0.5rem;
}
.pc-contra-side {
    padding: 0.75rem;
    border: 1px solid #fecaca;
    border-radius: 8px;
    background: #ffffff;
    font-size: 0.84rem;
    color: #475569;
    line-height: 1.5;
}
.pc-contra-pid {
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 0.8rem;
    font-weight: 600;
    color: #dc2626;
    margin-bottom: 0.35rem;
}

/* --- Responsive content width ------------------------------- */
@media (min-width: 1200px) {
    .pc-content-col {
        max-width: 820px;
    }
}

/* --- Chat input professional styling ----------------------- */
[data-testid="stChatInput"] {
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

/* --- Smooth transitions on interactive elements ------------ */
.pc-card, .pc-badge, .pc-citation-pill, .pc-prompt-chip,
.pc-claim-card, .pc-critic-card, .pc-contra-side {
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}
.pc-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* --- Better expander styling ------------------------------- */
div[data-testid="stExpander"] {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s;
}
div[data-testid="stExpander"]:hover {
    border-color: #cbd5e1;
}
div[data-testid="stExpander"] summary {
    font-weight: 550;
}

/* --- Download button polish -------------------------------- */
div[data-testid="stDownloadButton"] button {
    border-radius: 8px;
    font-weight: 550;
    transition: background 0.15s, transform 0.1s;
}
div[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-1px);
}

/* --- Entry animation for cards ----------------------------- */
@keyframes pc-fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
.pc-card, .pc-banner, .pc-claim-card, .pc-critic-card {
    animation: pc-fadeIn 0.25s ease-out;
}

/* --- Skeleton pulse for loading states --------------------- */
@keyframes pc-pulse {
    0%, 100% { opacity: 0.4; }
    50%      { opacity: 0.8; }
}
.pc-skeleton {
    background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
    background-size: 200% 100%;
    animation: pc-pulse 1.5s ease-in-out infinite;
    border-radius: 8px;
    height: 1rem;
    margin: 0.4rem 0;
}

/* --- Hero welcome card ------------------------------------- */
.pc-hero {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #dbeafe 100%);
    border: 1px solid #c7d2fe;
    border-radius: 16px;
    text-align: center;
    padding: 2.5rem 2rem 1.5rem 2rem;
    margin-bottom: 1.2rem;
}
.pc-hero h2 {
    font-size: 1.6rem;
    font-weight: 800;
    color: #1e293b;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.02em;
}
.pc-hero .pc-hero-tagline {
    color: #475569;
    font-size: 0.95rem;
    margin: 0 0 1.2rem 0;
    line-height: 1.5;
}
.pc-hero-capabilities {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    margin: 0.8rem auto;
    max-width: 520px;
    text-align: left;
}
.pc-hero-cap-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.84rem;
    color: #334155;
    padding: 0.5rem 0.75rem;
    background: rgba(255,255,255,0.7);
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}
.pc-hero-cap-icon {
    font-size: 1rem;
    color: #2563eb;
    flex-shrink: 0;
}

/* --- Sidebar mode descriptions ----------------------------- */
.pc-mode-desc {
    font-size: 0.72rem;
    color: #94a3b8;
    margin: -0.3rem 0 0.4rem 1.6rem;
    line-height: 1.35;
}

/* --- Quick Help sidebar panel ------------------------------ */
.pc-quick-help {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    font-size: 0.78rem;
    color: #475569;
    line-height: 1.5;
}
.pc-quick-help strong {
    color: #334155;
}

/* --- Footer ------------------------------------------------ */
.pc-footer {
    text-align: center;
    padding: 1.5rem 0 0.75rem 0;
    margin-top: 2rem;
    border-top: 1px solid #e2e8f0;
    font-size: 0.75rem;
    color: #94a3b8;
    letter-spacing: 0.01em;
}
.pc-footer strong {
    color: #64748b;
    font-weight: 600;
}

/* --- Abstention panel (upgraded) --------------------------- */
.pc-abstention-panel {
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    border: 1px solid #fde68a;
    border-left: 4px solid #d97706;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
}
.pc-abstention-panel h4 {
    margin: 0 0 0.4rem 0;
    color: #92400e;
    font-size: 0.95rem;
    font-weight: 700;
}
.pc-abstention-details {
    font-size: 0.84rem;
    color: #78350f;
    line-height: 1.55;
    margin: 0.3rem 0;
}
.pc-abstention-guidance {
    font-size: 0.82rem;
    color: #92400e;
    background: rgba(255,255,255,0.5);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    margin-top: 0.5rem;
    border: 1px solid #fde68a;
}

/* --- Help page --------------------------------------------- */
.pc-help-section {
    margin-bottom: 1.5rem;
}
.pc-glossary-term {
    font-weight: 700;
    color: #1e40af;
}
.pc-glossary-def {
    color: #475569;
    font-size: 0.9rem;
    margin-left: 0.5rem;
}
</style>"""
