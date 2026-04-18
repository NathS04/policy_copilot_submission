"""Generate PRISMA, Gantt, and data-flow diagrams for the dissertation."""
import os
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse, Rectangle
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def draw_prisma():
    """PRISMA 2020 flow diagram. Academic-journal style: muted greys with one
    accent for inclusion, square corners, thin borders, generous whitespace.
    Designed to read clearly at 6-inch print width."""
    fig, ax = plt.subplots(figsize=(11, 14.5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 15)
    ax.axis("off")

    main_face   = "#ffffff"
    excl_face   = "#f5f1ec"
    incl_face   = "#eef3ec"
    border      = "#3a3a3a"
    accent      = "#1f4d3a"
    excl_border = "#7a6a58"
    text_main   = "#1a1a1a"
    band        = "#f3f3f3"

    def box(x, y, w, h, text, face=main_face, edge=border,
            fontsize=10, bold=False, italic=False):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.04,rounding_size=0.04",
                              facecolor=face, edgecolor=edge, linewidth=1.0)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text,
                ha="center", va="center",
                fontsize=fontsize,
                weight="bold" if bold else "normal",
                style="italic" if italic else "normal",
                color=text_main,
                multialignment="center")

    def arrow(x1, y1, x2, y2, color=border, lw=1.1):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.25,head_length=0.5",
                                    color=color, lw=lw, shrinkA=0, shrinkB=0))

    # Left-side stage band (replaces the standalone text labels)
    ax.add_patch(plt.Rectangle((0.0, 0.0), 1.5, 15, facecolor=band,
                               edgecolor="none", zorder=0))

    stage_centres = [13.2, 10.5, 7.6, 4.6]  # IDENT, SCREEN, ELIG, INCL
    for label, yc in zip(
        ["IDENTIFICATION", "SCREENING", "ELIGIBILITY", "INCLUDED"], stage_centres
    ):
        ax.text(0.75, yc, label, fontsize=11.5, weight="bold", color=accent,
                ha="center", va="center", rotation=90, family="serif")

    # Vertical separator line on right edge of band
    ax.plot([1.5, 1.5], [0.2, 14.8], color=border, lw=0.7)

    # Stage 1 — Identification
    box(2.2, 12.4, 7.4, 1.5,
        "Records identified through database searching\n"
        "(Google Scholar, ACM Digital Library, IEEE Xplore, arXiv)\n"
        "$\\mathit{n}$ = 584",
        fontsize=10.5)

    arrow(5.9, 12.4, 5.9, 11.6)

    # Stage 2 — Screening: dedup
    box(2.2, 10.2, 5.0, 1.4,
        "Records after duplicates removed\n$\\mathit{n}$ = 472",
        fontsize=10.5)
    box(7.6, 10.2, 3.0, 1.4,
        "Duplicates removed\n$\\mathit{n}$ = 112",
        face=excl_face, edge=excl_border, fontsize=10)
    arrow(7.2, 10.9, 7.6, 10.9, color=excl_border)

    arrow(4.7, 10.2, 4.7, 9.4)

    # Stage 2 — title/abstract screening
    box(2.2, 8.0, 5.0, 1.4,
        "Records screened by title and abstract\n$\\mathit{n}$ = 472",
        fontsize=10.5)
    box(7.6, 7.7, 3.0, 1.7,
        "Records excluded\n(off-topic, no empirical\nevaluation, no retrieval)\n"
        "$\\mathit{n}$ = 318",
        face=excl_face, edge=excl_border, fontsize=10)
    arrow(7.2, 8.7, 7.6, 8.7, color=excl_border)

    arrow(4.7, 8.0, 4.7, 7.2)

    # Stage 3 — Eligibility
    box(2.2, 5.5, 5.0, 1.7,
        "Full-text articles assessed for eligibility\n$\\mathit{n}$ = 154",
        fontsize=10.5)
    box(7.6, 4.9, 3.2, 2.3,
        "Full-text articles excluded ($\\mathit{n}$ = 116)\n"
        "\u2022 Insufficient verification focus  62\n"
        "\u2022 Purely open-domain scope     31\n"
        "\u2022 No empirical baselines              23",
        face=excl_face, edge=excl_border, fontsize=9.5)
    arrow(7.2, 6.05, 7.6, 6.05, color=excl_border)

    arrow(4.7, 5.5, 4.7, 4.7)

    # Stage 4 — Included
    box(2.2, 3.0, 5.0, 1.7,
        "Studies included in qualitative synthesis\n"
        "$\\mathit{n}$ = 38",
        face=incl_face, edge=accent, fontsize=11.5, bold=True)

    # Footer note (small print, journal style)
    ax.text(5.5, 1.3,
            "Adapted from the PRISMA 2020 flow diagram template (Page et al., 2021).",
            ha="center", va="center", fontsize=8.5, style="italic", color="#555555",
            family="serif")

    fig.savefig(OUT / "fig_prisma.png", dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved {OUT / 'fig_prisma.png'}")


def draw_gantt():
    """Six-sprint Gantt chart in a single muted blue tone with a parallel
    documentation strip. Restrained palette, no rainbow."""
    fig, ax = plt.subplots(figsize=(11.5, 5.2))

    sprints = [
        ("S1  Corpus Engineering",  1,  3),
        ("S2  Retrieval Pipeline",  4,  6),
        ("S3  Generative Pipeline", 7,  9),
        ("S4  Reliability Layers", 10, 14),
        ("S5  Critic Mode",        15, 17),
        ("S6  Evaluation Harness", 18, 22),
    ]

    bar_color    = "#3b6c8b"   # muted slate blue
    docs_color   = "#a8a8a8"   # warm grey for the parallel docs strip
    grid_color   = "#dddddd"
    text_main    = "#1a1a1a"

    rows = list(range(len(sprints), 0, -1))  # 6,5,4,3,2,1 (top → bottom)
    docs_row = 0  # parallel documentation strip below sprint rows

    for (name, start, end), y in zip(sprints, rows):
        duration = end - start + 1
        ax.barh(y, duration, left=start - 0.5, height=0.55,
                color=bar_color, edgecolor="white", linewidth=0.6)
        ax.text(start + duration / 2 - 0.5, y,
                f"Wk {start}\u2013{end}", ha="center", va="center",
                fontsize=9, color="white", family="serif")

    # Parallel documentation strip (real continuous activity per §2.1)
    ax.barh(docs_row, 22, left=0.5, height=0.45,
            color=docs_color, edgecolor="white", linewidth=0.6, alpha=0.85)
    ax.text(11, docs_row, "Documentation, evaluation refinement, report writing",
            ha="center", va="center", fontsize=8.5, color="white",
            style="italic", family="serif")

    yticks = [docs_row] + rows
    yticklabels = ["  Continuous"] + [s[0] for s in sprints]
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels, fontsize=9.5, family="serif")
    ax.set_xlabel("Project week", fontsize=10, family="serif")
    ax.set_xlim(0.5, 22.5)
    ax.set_ylim(-0.7, len(sprints) + 0.7)
    ax.set_xticks(range(1, 23))
    ax.set_xticklabels(range(1, 23), fontsize=7.5)
    ax.tick_params(axis="x", length=2, pad=2)
    ax.tick_params(axis="y", length=0, pad=4)

    # Subtle vertical month separators (no big rainbow lines)
    month_labels = [
        (1, "Oct 2024"), (5, "Nov"), (9, "Dec"),
        (13, "Jan 2025"), (17, "Feb"), (21, "Mar"),
    ]
    for wk, _ in month_labels:
        ax.axvline(x=wk - 0.5, color=grid_color, linestyle="-",
                   linewidth=0.5, zorder=0)
    for wk, label in month_labels:
        ax.text(wk - 0.5, len(sprints) + 0.5, label, fontsize=7.5,
                color="#666666", family="serif", ha="left")

    # Clean spines: keep bottom and left only
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color("#888888")
        ax.spines[s].set_linewidth(0.6)

    fig.savefig(OUT / "fig_gantt.png", dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved {OUT / 'fig_gantt.png'}")


def draw_dataflow():
    """Policy Copilot end-to-end architecture as a horizontal-swimlane
    systems diagram. Distinct shape language (cylinders for stores,
    rectangles for processes, diamond for the decision gate, parallelogram
    for the verified output), restrained palette, real module names from
    ``src/policy_copilot/``."""
    fig, ax = plt.subplots(figsize=(11.5, 11))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 14)
    ax.axis("off")

    # Palette --------------------------------------------------------
    proc_face   = "#f7f7f7"
    proc_edge   = "#3a3a3a"
    store_face  = "#ebebeb"
    store_edge  = "#555555"
    decision_face = "#f3e9d2"
    decision_edge = "#8a6a2e"
    abstain_face  = "#f3e9d2"
    abstain_edge  = "#8a6a2e"
    verify_face = "#e8f0e9"
    verify_edge = "#2f5d3a"
    text_main   = "#1a1a1a"
    arrow_color = "#2a2a2a"

    # Lane bands -----------------------------------------------------
    lanes = [
        ("Output and audit",      0.6,  2.4,  "#fafafa"),
        ("Decision and generation", 2.4,  6.6,  "#f4f4f4"),
        ("Per-query retrieval",   6.6, 10.0, "#fafafa"),
        ("Offline ingestion",    10.0, 13.4, "#f4f4f4"),
    ]
    for label, y0, y1, fill in lanes:
        ax.add_patch(Rectangle(
            (0, y0), 12, y1 - y0,
            facecolor=fill, edgecolor="none", zorder=0,
        ))
        ax.plot([0, 12], [y0, y0], color="#cccccc", lw=0.5, zorder=0)
        ax.text(0.20, (y0 + y1) / 2, label,
                fontsize=10, weight="bold", color="#666666",
                family="serif",
                rotation=90, ha="center", va="center")
    ax.plot([0, 12], [13.4, 13.4], color="#cccccc", lw=0.5, zorder=0)

    # Helpers --------------------------------------------------------
    def proc_box(x, y, w, h, title, sub="", *, face=proc_face, edge=proc_edge,
                 title_size=10.5, sub_size=8.5, bold=True):
        rect = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.06",
            facecolor=face, edgecolor=edge, linewidth=1.1, zorder=2,
        )
        ax.add_patch(rect)
        if sub:
            ax.text(x + w / 2, y + h * 0.66, title,
                    ha="center", va="center",
                    fontsize=title_size, weight="bold" if bold else "normal",
                    color=text_main, family="serif")
            ax.text(x + w / 2, y + h * 0.30, sub,
                    ha="center", va="center", fontsize=sub_size,
                    color="#3a3a3a", family="serif", style="italic",
                    multialignment="center")
        else:
            ax.text(x + w / 2, y + h / 2, title,
                    ha="center", va="center",
                    fontsize=title_size, weight="bold" if bold else "normal",
                    color=text_main, family="serif",
                    multialignment="center")

    def cylinder(cx, cy, w, h, title, sub=""):
        # Stylised cylinder: a rectangle for the body, two ellipses for
        # the top and bottom rims. Uses store palette.
        ry = 0.18
        # body
        ax.add_patch(Rectangle(
            (cx - w/2, cy - h/2 + ry), w, h - 2*ry,
            facecolor=store_face, edgecolor=store_edge, linewidth=1.0, zorder=2,
        ))
        # bottom curve
        ax.add_patch(Ellipse(
            (cx, cy - h/2 + ry), width=w, height=2*ry,
            facecolor=store_face, edgecolor=store_edge, linewidth=1.0, zorder=2,
        ))
        # top curve
        ax.add_patch(Ellipse(
            (cx, cy + h/2 - ry), width=w, height=2*ry,
            facecolor=store_face, edgecolor=store_edge, linewidth=1.0, zorder=2,
        ))
        # mask the upper half of the bottom ellipse so we get the side wall look
        ax.add_patch(Rectangle(
            (cx - w/2 - 0.001, cy - h/2 + ry), w + 0.002, h - 2*ry,
            facecolor=store_face, edgecolor="none", zorder=2.5,
        ))
        # re-draw side walls on top
        ax.plot([cx - w/2, cx - w/2], [cy - h/2 + ry, cy + h/2 - ry],
                color=store_edge, lw=1.0, zorder=2.6)
        ax.plot([cx + w/2, cx + w/2], [cy - h/2 + ry, cy + h/2 - ry],
                color=store_edge, lw=1.0, zorder=2.6)
        # re-draw top ellipse on top of mask for the visible front rim
        ax.add_patch(Ellipse(
            (cx, cy + h/2 - ry), width=w, height=2*ry,
            facecolor=store_face, edgecolor=store_edge, linewidth=1.0, zorder=2.7,
        ))
        # labels
        if sub:
            ax.text(cx, cy + 0.10, title, ha="center", va="center",
                    fontsize=10.5, weight="bold", color=text_main,
                    family="serif", zorder=3)
            ax.text(cx, cy - 0.20, sub, ha="center", va="center",
                    fontsize=8.5, color="#3a3a3a", family="serif",
                    style="italic", zorder=3)
        else:
            ax.text(cx, cy, title, ha="center", va="center",
                    fontsize=10.5, weight="bold", color=text_main,
                    family="serif", zorder=3)

    def diamond(cx, cy, w, h, title, sub=""):
        pts = [(cx, cy + h/2), (cx + w/2, cy), (cx, cy - h/2), (cx - w/2, cy)]
        poly = Polygon(pts, closed=True,
                       facecolor=decision_face, edgecolor=decision_edge,
                       linewidth=1.1, zorder=2)
        ax.add_patch(poly)
        if sub:
            ax.text(cx, cy + 0.18, title, ha="center", va="center",
                    fontsize=10.5, weight="bold", color=text_main,
                    family="serif", zorder=3)
            ax.text(cx, cy - 0.18, sub, ha="center", va="center",
                    fontsize=8.5, color="#3a3a3a", family="serif",
                    style="italic", zorder=3)
        else:
            ax.text(cx, cy, title, ha="center", va="center",
                    fontsize=10.5, weight="bold", color=text_main,
                    family="serif", zorder=3)

    def parallelogram(x, y, w, h, title, sub=""):
        skew = 0.3
        pts = [
            (x + skew, y), (x + w, y),
            (x + w - skew, y + h), (x, y + h),
        ]
        poly = Polygon(pts, closed=True,
                       facecolor=verify_face, edgecolor=verify_edge,
                       linewidth=1.2, zorder=2)
        ax.add_patch(poly)
        if sub:
            ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
                    fontsize=11, weight="bold", color=text_main,
                    family="serif", zorder=3)
            ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center",
                    fontsize=8.5, color="#3a3a3a", family="serif",
                    style="italic", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                    fontsize=11, weight="bold", color=text_main,
                    family="serif", zorder=3)

    def arrow(x1, y1, x2, y2, *, color=arrow_color, lw=1.1,
              label=None, label_offset=(0.1, 0.05), label_color=None):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>,head_width=0.25,head_length=0.5",
                            color=color, lw=lw, shrinkA=0, shrinkB=0),
            zorder=2.5,
        )
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx + label_offset[0], my + label_offset[1], label,
                    fontsize=8, color=label_color or "#555555",
                    family="serif", style="italic", zorder=3)

    # --- Offline ingestion lane (top, y in 10.0..13.4) -------------
    cylinder(2.8, 11.7, 2.6, 1.5, "PDF corpus",
             "policy handbook,\nIT addendum, etc.")
    proc_box(5.0, 11.0, 3.2, 1.4,
             "Ingestion",
             "ingest.parse_pdf  \u2192  chunk\nstable IDs (SHA-256)")
    cylinder(9.6, 11.7, 2.4, 1.5, "Paragraph store",
             "doc::page::idx::hash")
    arrow(4.1, 11.7, 5.0, 11.7)
    arrow(8.2, 11.7, 8.4, 11.7)
    arrow(9.6, 10.95, 9.6, 9.6, label="paragraphs", label_offset=(0.10, 0.05))

    # --- Per-query retrieval lane (y in 6.6..10.0) -----------------
    # Input shape: parallelogram (data flow input convention).
    qpts = [
        (1.0, 7.7), (3.4, 7.7), (3.1, 8.9), (0.7, 8.9),
    ]
    ax.add_patch(Polygon(qpts, closed=True,
                         facecolor="#ebebeb", edgecolor=store_edge,
                         linewidth=1.0, zorder=2))
    ax.text(2.05, 8.45, "User query", ha="center", va="center",
            fontsize=10.5, weight="bold", color=text_main,
            family="serif", zorder=3)
    ax.text(2.05, 8.10, "natural language", ha="center", va="center",
            fontsize=8.5, color="#3a3a3a", family="serif",
            style="italic", zorder=3)

    proc_box(5.0, 7.6, 3.2, 1.4,
             "Dense retrieval",
             "all-MiniLM-L6-v2 + FAISS\ntop-20 candidates")
    proc_box(8.6, 7.6, 3.0, 1.4,
             "Cross-encoder rerank",
             "ms-marco-MiniLM-L-6-v2\ntop-5 + score")
    arrow(3.4, 8.3, 5.0, 8.3, label="NL question", label_offset=(0.10, 0.06))
    arrow(8.2, 8.3, 8.6, 8.3)
    arrow(9.6, 9.6, 6.6, 8.95, label="paragraphs", label_offset=(0.10, 0.05))

    # --- Decision and generation lane (y in 2.4..6.6) -------------
    diamond(5.5, 5.2, 2.4, 1.4,
            "Abstention gate",
            "score \u2265 0.30 ?")
    arrow(6.6, 7.6, 6.0, 5.9, label="confidence",
          label_offset=(0.04, 0.10))

    # Abstention output (right of decision diamond)
    proc_box(8.6, 4.7, 3.0, 1.0,
             "INSUFFICIENT EVIDENCE",
             "FALLBACK_RELEVANCE_FAIL",
             face=abstain_face, edge=abstain_edge,
             title_size=10.5, sub_size=8)
    arrow(6.7, 5.2, 8.6, 5.2, color=abstain_edge,
          label="below \u03c4", label_offset=(0.0, 0.10),
          label_color=abstain_edge)

    # Generation below the diamond
    proc_box(4.0, 3.0, 3.2, 1.4,
             "Answer generator",
             "OpenAI \u00b7 Anthropic\nPydantic JSON schema")
    arrow(5.5, 4.5, 5.5, 4.4, label="above \u03c4", label_offset=(0.05, 0.05))
    arrow(5.5, 4.5, 5.5, 4.4)

    # --- Verification + contradiction in same lane -----------------
    proc_box(7.6, 3.0, 3.2, 1.4,
             "Per-claim verifier",
             "Jaccard \u2265 0.10  \u00b7  numeric\nsupport policy  \u00b7  pruning")
    arrow(7.2, 3.7, 7.6, 3.7, label="claims+citations",
          label_offset=(0.05, 0.10))

    proc_box(0.5, 3.0, 3.0, 1.4,
             "Contradiction detector",
             "antonym \u00b7 numeric \u00b7 negation",
             title_size=10, sub_size=8)
    arrow(4.0, 3.7, 3.5, 3.7, label="claims",
          label_offset=(-0.4, 0.10))

    # --- Output and audit lane (y in 0.6..2.4) --------------------
    parallelogram(3.5, 0.85, 5.0, 1.2,
                  "Verified answer + audit trail",
                  "answer \u00b7 citations \u00b7 contradiction notes")
    # Single consolidated arrow from the verifier to the output. The
    # abstention path is shown as a dashed connector that goes off the
    # right edge of the diagram (outside the verifier), down, and back
    # into the audit-trail parallelogram from the right.
    arrow(9.2, 3.0, 7.5, 2.05, label="if all claims pass",
          label_offset=(-1.5, -0.05))
    # Right-routed dashed abstention connector (3 segments)
    abstain_path = [
        (10.1, 4.7),   # leaving INSUFFICIENT_EVIDENCE south edge
        (11.6, 4.7),
        (11.6, 1.45),
        (8.5, 1.45),   # arriving at parallelogram east edge
    ]
    for (x0, y0), (x1, y1) in zip(abstain_path[:-1], abstain_path[1:]):
        ax.plot([x0, x1], [y0, y1], color=abstain_edge,
                lw=1.0, linestyle=(0, (4, 2)), zorder=2.4)
    ax.annotate(
        "", xy=(8.5, 1.45), xytext=(8.7, 1.45),
        arrowprops=dict(arrowstyle="-|>,head_width=0.22,head_length=0.45",
                        color=abstain_edge, lw=1.0, shrinkA=0, shrinkB=0),
        zorder=2.5,
    )
    ax.text(11.7, 3.0, "if abstained",
            fontsize=8, color=abstain_edge, family="serif", style="italic",
            rotation=90, ha="center", va="center", zorder=3)

    # Module-level note
    ax.text(11.95, 0.05,
            "Modules: src/policy_copilot/{ingest, retrieve, rerank, "
            "abstain, generate, verify, contradiction}",
            fontsize=7, color="#777777", family="serif",
            ha="right", va="bottom")

    fig.savefig(OUT / "fig_data_flow.png", dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved {OUT / 'fig_data_flow.png'}")


def draw_dataflow_OLD():
    """End-to-end Policy Copilot architecture: top-to-bottom flow with
    sharp rectangles, restrained greys, and one accent for the abstention
    branch and one for the verified output. Project-specific labels with
    real module names from src/policy_copilot/."""
    fig, ax = plt.subplots(figsize=(11.5, 11))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 13)
    ax.axis("off")

    # Restrained palette: greyscale + one warm accent (abstention) + one
    # cool accent (verified output). Everything else is monochrome.
    process_face   = "#f7f7f7"
    process_edge   = "#3a3a3a"
    abstain_face   = "#f3e9d2"
    abstain_edge   = "#8a6a2e"
    verify_face    = "#e8f0e9"
    verify_edge    = "#2f5d3a"
    store_face     = "#ebebeb"
    store_edge     = "#555555"
    text_main      = "#1a1a1a"
    arrow_color    = "#2a2a2a"

    def box(x, y, w, h, title, sub="", *,
            face=process_face, edge=process_edge,
            title_size=10.5, sub_size=8.5, bold=True, italic_sub=True):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.04,rounding_size=0.06",
                              facecolor=face, edgecolor=edge, linewidth=1.1)
        ax.add_patch(rect)
        if sub:
            ax.text(x + w / 2, y + h * 0.66, title,
                    ha="center", va="center",
                    fontsize=title_size, weight="bold" if bold else "normal",
                    color=text_main, family="serif")
            ax.text(x + w / 2, y + h * 0.30, sub,
                    ha="center", va="center",
                    fontsize=sub_size,
                    color="#3a3a3a", family="serif",
                    style="italic" if italic_sub else "normal",
                    multialignment="center")
        else:
            ax.text(x + w / 2, y + h / 2, title,
                    ha="center", va="center",
                    fontsize=title_size, weight="bold" if bold else "normal",
                    color=text_main, family="serif",
                    multialignment="center")

    def arrow(x1, y1, x2, y2, *, color=arrow_color, lw=1.1, label=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.25,head_length=0.5",
                                    color=color, lw=lw, shrinkA=0, shrinkB=0))
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx + 0.08, my, label, fontsize=8, family="serif",
                    color="#555555", style="italic")

    # ----- Top: ingestion lane ------------------------------------------
    box(0.4, 11.4, 2.8, 1.1, "PDF Corpus",
        "policy handbook,\nIT addendum, etc.",
        face=store_face, edge=store_edge, sub_size=8)
    box(4.2, 11.4, 3.4, 1.1, "Ingestion",
        "ingest.parse_pdf  \u2192  chunk\nstable IDs (SHA-256)")
    box(8.6, 11.4, 3.0, 1.1, "Paragraph store",
        "doc::page::idx::hash",
        face=store_face, edge=store_edge, sub_size=8)
    arrow(3.2, 11.95, 4.2, 11.95)
    arrow(7.6, 11.95, 8.6, 11.95)

    # ----- Query lane ---------------------------------------------------
    box(0.4, 9.5, 2.8, 1.1, "User query",
        "natural language",
        face=store_face, edge=store_edge, sub_size=8)

    # ----- Retrieval ----------------------------------------------------
    box(4.2, 9.5, 3.4, 1.1, "Dense retrieval",
        "all-MiniLM-L6-v2 + FAISS\ntop-20 candidates")
    arrow(3.2, 10.05, 4.2, 10.05)
    # paragraph store feeds retriever
    arrow(10.1, 11.4, 6.5, 10.6)

    # ----- Reranker -----------------------------------------------------
    box(4.2, 7.7, 3.4, 1.1, "Cross-encoder rerank",
        "ms-marco-MiniLM-L-6-v2\ntop-5 + confidence score")
    arrow(5.9, 9.5, 5.9, 8.8)

    # Confidence flows down to the gate
    box(4.2, 5.9, 3.4, 1.1, "Abstention gate",
        "score \u2265 0.30 ? \u2014 decided\n\u2003before\u2003 any LLM call",
        face=abstain_face, edge=abstain_edge)
    arrow(5.9, 7.7, 5.9, 7.0)

    # ----- Abstention branch (right) -----------------------------------
    box(8.6, 5.9, 3.0, 1.1, "INSUFFICIENT\nEVIDENCE",
        "FALLBACK_RELEVANCE_FAIL",
        face=abstain_face, edge=abstain_edge, title_size=11, sub_size=8)
    arrow(7.6, 6.45, 8.6, 6.45, color=abstain_edge,
          label="below\u2003threshold")

    # ----- Generative path (left) --------------------------------------
    box(4.2, 4.0, 3.4, 1.1, "Answer generator",
        "OpenAI \u00b7 Anthropic\nPydantic JSON schema")
    arrow(5.9, 5.9, 5.9, 5.1, label="above\u2003threshold")

    # ----- Verification -------------------------------------------------
    box(4.2, 2.1, 3.4, 1.2, "Per-claim verifier",
        "Jaccard \u2265 0.10  \u00b7  numeric check\nsupport policy  \u00b7  claim pruning")
    arrow(5.9, 4.0, 5.9, 3.3)

    # ----- Contradiction detector (right of verifier) ------------------
    box(8.6, 2.1, 3.0, 1.2, "Contradiction\ndetection",
        "antonym \u00b7 numeric \u00b7 negation",
        face=process_face, edge=process_edge, title_size=10, sub_size=8)
    arrow(7.6, 2.7, 8.6, 2.7)

    # ----- Final output ------------------------------------------------
    box(4.2, 0.3, 3.4, 1.0, "Verified answer + audit trail",
        face=verify_face, edge=verify_edge, title_size=11)
    arrow(5.9, 2.1, 5.9, 1.3)

    # ----- Extractive fallback edge (alternate path) -------------------
    # Diagonal from rerank output to answer generator with an annotation.
    ax.annotate(
        "Extractive Mode  \u2014  bypass LLM,\nreturn top reranked paragraph verbatim",
        xy=(7.6, 4.55), xytext=(7.95, 8.0),
        fontsize=8, color="#555555", family="serif", style="italic",
        ha="left", va="center",
        arrowprops=dict(arrowstyle="-|>,head_width=0.2,head_length=0.4",
                         color="#888888", lw=0.8,
                         connectionstyle="arc3,rad=0.25",
                         shrinkA=0, shrinkB=0)
    )

    # ----- Lane label on left edge -------------------------------------
    ax.text(0.05, 12.0, "Offline / one-time", fontsize=8,
            color="#888888", family="serif", rotation=90,
            ha="center", va="top")
    ax.text(0.05, 7.5, "Per-query path", fontsize=8,
            color="#888888", family="serif", rotation=90,
            ha="center", va="center")

    # Module-level note
    ax.text(11.6, 0.1,
            "Modules: src/policy_copilot/{ingest, retrieve, rerank, "
            "abstain, generate, verify, contradiction}",
            fontsize=7, color="#777777", family="serif",
            ha="right", va="bottom")

    fig.savefig(OUT / "fig_data_flow.png", dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved {OUT / 'fig_data_flow.png'}")


def draw_screenshots():
    """Generate clean UI mockup screenshots for the three query types."""

    def make_screenshot(filename, query, response_type, response_text,
                        citations=None, badge_color="#27ae60", badge_text="Supported"):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis("off")
        fig.set_facecolor("#1a1a2e")

        # Header bar
        header = FancyBboxPatch((0.1, 5.2), 9.8, 0.6, boxstyle="round,pad=0.05",
                                facecolor="#16213e", edgecolor="#0f3460", linewidth=1)
        ax.add_patch(header)
        ax.text(0.5, 5.5, "Policy Copilot", fontsize=14, color="white",
                weight="bold", va="center")
        ax.text(3.5, 5.5, "Ask", fontsize=10, color="#e94560", weight="bold", va="center")
        ax.text(4.5, 5.5, "Audit Trace", fontsize=10, color="#aaa", va="center")
        ax.text(6.0, 5.5, "Critic Lens", fontsize=10, color="#aaa", va="center")

        # Query box
        qbox = FancyBboxPatch((0.3, 4.3), 9.4, 0.7, boxstyle="round,pad=0.08",
                               facecolor="#0f3460", edgecolor="#1a1a4e", linewidth=0.8)
        ax.add_patch(qbox)
        ax.text(0.6, 4.65, f"Q: {query}", fontsize=10, color="#e0e0e0", va="center")

        # Badge
        badge = FancyBboxPatch((0.5, 3.7), 1.8, 0.4, boxstyle="round,pad=0.05",
                                facecolor=badge_color, edgecolor="none")
        ax.add_patch(badge)
        ax.text(1.4, 3.9, badge_text, fontsize=9, color="white",
                weight="bold", ha="center", va="center")

        # Response card
        rbox = FancyBboxPatch((0.3, 0.5), 9.4, 3.0, boxstyle="round,pad=0.1",
                               facecolor="#16213e", edgecolor="#1a1a4e", linewidth=0.8)
        ax.add_patch(rbox)
        ax.text(0.6, 3.15, response_text, fontsize=9, color="#d0d0d0",
                va="top", wrap=True, multialignment="left",
                fontfamily="monospace")

        if citations:
            for i, cit in enumerate(citations):
                cx = 0.6 + i * 2.5
                pill = FancyBboxPatch((cx, 0.7), 2.2, 0.3, boxstyle="round,pad=0.05",
                                      facecolor="#0f3460", edgecolor="#4472c4", linewidth=0.5)
                ax.add_patch(pill)
                ax.text(cx + 1.1, 0.85, cit, fontsize=7, color="#7eb0d5",
                        ha="center", va="center")

        fig.savefig(OUT / filename, dpi=200, bbox_inches="tight",
                    facecolor="#1a1a2e", edgecolor="none")
        plt.close(fig)
        print(f"Saved {OUT / filename}")

    make_screenshot(
        "screenshot_answerable_query.png",
        "What is the company's remote work policy?",
        "answerable",
        "Employees may work remotely for up to three consecutive\n"
        "days per week, subject to manager approval. Remote work\n"
        "arrangements must be documented in writing and reviewed\n"
        "quarterly. [handbook::3::2::a4f8c1]",
        citations=["handbook::3::2::a4f8c1", "handbook::3::4::b2e1d9"],
        badge_color="#27ae60",
        badge_text="Supported"
    )

    make_screenshot(
        "screenshot_unanswerable_query.png",
        "What is the GDP of France in 2024?",
        "unanswerable",
        "INSUFFICIENT_EVIDENCE\n\n"
        "The corpus does not contain enough information\n"
        "to answer this question. The query falls outside\n"
        "the scope of the policy document corpus.\n\n"
        "Note: FALLBACK_RELEVANCE_FAIL — max reranker\n"
        "score below confidence threshold (0.30).",
        badge_color="#e74c3c",
        badge_text="Abstained"
    )

    make_screenshot(
        "screenshot_contradiction_query.png",
        "How often must passwords be changed?",
        "contradiction",
        "Password rotation requirements differ across\n"
        "policy documents:\n\n"
        "  • Employee Handbook (§4.2): \"every 90 days\"\n"
        "  • IT Security Addendum (§2.1): \"every 60 days\"\n\n"
        "⚠ CONTRADICTION DETECTED between these sources.\n"
        "Consult your IT administrator for clarification.",
        citations=["handbook::4::2::c3d2e1", "security::2::1::f7a8b3"],
        badge_color="#f39c12",
        badge_text="Contradiction"
    )


if __name__ == "__main__":
    draw_prisma()
    draw_gantt()
    draw_dataflow()
    draw_screenshots()
    print("\nAll diagrams generated successfully.")
