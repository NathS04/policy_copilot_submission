"""Generate PRISMA, Gantt, and data-flow diagrams for the dissertation."""
import os
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def draw_prisma():
    fig, ax = plt.subplots(figsize=(10, 13))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")

    box_color = "#dce6f1"
    excl_color = "#f2dcdb"
    incl_color = "#d5e8d4"
    edge_color = "#4472c4"

    def box(x, y, w, h, text, color=box_color, fontsize=9, bold=False):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                              facecolor=color, edgecolor=edge_color, linewidth=1.2)
        ax.add_patch(rect)
        weight = "bold" if bold else "normal"
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=fontsize, weight=weight, wrap=True,
                multialignment="center")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle="-|>", color=edge_color, lw=1.5))

    def side_arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle="-|>", color="#c0504d", lw=1.2))

    # Stage labels
    ax.text(0.3, 13.2, "IDENTIFICATION", fontsize=11, weight="bold", color=edge_color)
    ax.text(0.3, 10.7, "SCREENING", fontsize=11, weight="bold", color=edge_color)
    ax.text(0.3, 8.0, "ELIGIBILITY", fontsize=11, weight="bold", color=edge_color)
    ax.text(0.3, 5.0, "INCLUDED", fontsize=11, weight="bold", color=edge_color)

    # Stage 1
    box(1.5, 12.0, 7, 1.0,
        "Records identified through\ndatabase searching\n(Google Scholar, ACM DL, IEEE Xplore, arXiv)\nn = 584",
        fontsize=9.5)

    arrow(5, 12.0, 5, 11.2)

    # Stage 2
    box(1.5, 10.0, 4.5, 1.0,
        "Records after duplicates\nremoved\nn = 472", fontsize=9.5)
    box(6.5, 10.0, 3, 1.0,
        "Duplicates removed\nn = 112", color=excl_color, fontsize=9)
    side_arrow(6.0, 10.5, 6.5, 10.5)

    arrow(3.75, 10.0, 3.75, 9.2)

    box(1.5, 8.0, 4.5, 1.0,
        "Records screened by\ntitle and abstract\nn = 472", fontsize=9.5)
    box(6.5, 8.0, 3, 1.0,
        "Records excluded\n(off-topic, no eval,\nno retrieval)\nn = 318",
        color=excl_color, fontsize=8.5)
    side_arrow(6.0, 8.5, 6.5, 8.5)

    arrow(3.75, 8.0, 3.75, 7.2)

    # Stage 3
    box(1.5, 5.8, 4.5, 1.2,
        "Full-text articles\nassessed for eligibility\nn = 154", fontsize=9.5)
    box(6.5, 5.5, 3, 1.8,
        "Full-text excluded (n = 116)\n\nInsufficient verification\nfocus: n = 62\n\nPurely open-domain: n = 31\n\nNo empirical baselines: n = 23",
        color=excl_color, fontsize=7.8)
    side_arrow(6.0, 6.4, 6.5, 6.4)

    arrow(3.75, 5.8, 3.75, 5.0)

    # Stage 4
    box(1.5, 3.8, 4.5, 1.0,
        "Studies included in\nqualitative synthesis\nn = 38",
        color=incl_color, fontsize=10, bold=True)

    # No baked-in title; the markdown caption supplies the figure title in the report.
    fig.savefig(OUT / "fig_prisma.png", dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved {OUT / 'fig_prisma.png'}")


def draw_gantt():
    fig, ax = plt.subplots(figsize=(12, 5))

    sprints = [
        ("S1: Corpus Engineering", 1, 3),
        ("S2: Retrieval Pipeline", 4, 6),
        ("S3: Generative Pipeline", 7, 9),
        ("S4: Reliability Layers", 10, 14),
        ("S5: Critic Mode", 15, 17),
        ("S6: Evaluation Harness", 18, 22),
    ]

    colors = ["#4472c4", "#5b9bd5", "#70ad47", "#ed7d31", "#ffc000", "#c0504d"]
    month_labels = [
        (1, "Oct 2024"), (4, "Nov"), (7, "Dec"),
        (10, "Jan 2025"), (14, "Feb"), (18, "Mar"),
    ]

    y_positions = list(range(len(sprints) - 1, -1, -1))

    for i, (name, start, end) in enumerate(sprints):
        duration = end - start + 1
        ax.barh(y_positions[i], duration, left=start - 0.5, height=0.6,
                color=colors[i], edgecolor="white", linewidth=0.5, alpha=0.9)
        ax.text(start + duration / 2 - 0.5, y_positions[i],
                f"Wk {start}–{end}", ha="center", va="center",
                fontsize=8, color="white", weight="bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([s[0] for s in sprints], fontsize=9)
    ax.set_xlabel("Week", fontsize=10)
    ax.set_xlim(0.5, 22.5)
    ax.set_xticks(range(1, 23))
    ax.set_xticklabels(range(1, 23), fontsize=7)

    for wk, label in month_labels:
        ax.axvline(x=wk - 0.5, color="#cccccc", linestyle="--", linewidth=0.5)
        ax.text(wk - 0.3, len(sprints) - 0.3, label, fontsize=7, color="#666666")

    # No baked-in title; the markdown caption supplies the figure title in the report.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.savefig(OUT / "fig_gantt.png", dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved {OUT / 'fig_gantt.png'}")


def draw_dataflow():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    blue = "#dce6f1"
    green = "#d5e8d4"
    orange = "#fce5cd"
    red = "#f2dcdb"
    blue_edge = "#4472c4"
    green_edge = "#548235"
    orange_edge = "#c55a11"
    red_edge = "#c0504d"

    def box(x, y, w, h, text, fcolor, ecolor, fontsize=8.5, bold=False):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                              facecolor=fcolor, edgecolor=ecolor, linewidth=1.3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center",
                fontsize=fontsize, weight="bold" if bold else "normal",
                multialignment="center")

    def arrow(x1, y1, x2, y2, color=blue_edge):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5))

    # Row 1: Input
    box(0.3, 7.5, 2.5, 1.0, "PDF Policy\nCorpus", blue, blue_edge, bold=True)
    arrow(2.8, 8.0, 3.5, 8.0)
    box(3.5, 7.5, 2.5, 1.0, "INGESTION\nParse → Chunk → Hash IDs", blue, blue_edge)
    arrow(6.0, 8.0, 6.8, 8.0)
    box(6.8, 7.5, 2.5, 1.0, "Paragraph\nStore", blue, blue_edge)

    # Row 2: Retrieval
    box(0.3, 5.8, 2.5, 1.0, "User\nQuery", green, green_edge, bold=True)
    arrow(2.8, 6.3, 3.5, 6.3)
    box(3.5, 5.8, 2.5, 1.0, "RETRIEVAL\nBi-encoder + FAISS/BM25\nTop-20 candidates", blue, blue_edge)
    arrow(6.0, 6.3, 6.8, 6.3)
    box(6.8, 5.8, 2.5, 1.0, "RERANKING\nCross-encoder\nTop-5 + Score", blue, blue_edge)

    # Paragraph store feeds retrieval
    arrow(8.05, 7.5, 8.05, 6.8, color=blue_edge)

    # Row 3: Abstention gate
    arrow(8.05, 5.8, 8.05, 5.0)
    box(6.8, 4.0, 2.5, 0.9, "ABSTENTION\nGATE\n(threshold = 0.30)", orange, orange_edge, bold=True)

    # Abstention output
    arrow(9.3, 4.45, 10.2, 4.45, color=red_edge)
    box(10.2, 4.0, 3.2, 0.9, "INSUFFICIENT\nEVIDENCE", red, red_edge, bold=True)

    # Pass through gate
    arrow(8.05, 4.0, 8.05, 3.2)

    # Row 4: Generation
    box(6.0, 2.0, 3.2, 1.0, "GENERATION\nLLM + Citation Enforcement\nPydantic Schema", green, green_edge)

    # Row 5: Verification
    arrow(7.6, 2.0, 7.6, 1.2)
    box(5.5, 0.2, 4.2, 0.9, "VERIFICATION\nJaccard Overlap · Numeric Check\nClaim Pruning · Support Policy", orange, orange_edge)

    # Final output
    arrow(9.7, 0.65, 10.8, 0.65, color=green_edge)
    box(10.8, 0.2, 2.8, 0.9, "Verified Answer\n+ Audit Trail", green, green_edge, bold=True)

    # Contradiction detection branch
    box(10.5, 5.8, 3.0, 1.0, "CONTRADICTION\nDETECTION\nAntonym/Negation/Numeric", orange, orange_edge)
    arrow(9.3, 6.3, 10.5, 6.3, color=orange_edge)
    arrow(12.0, 5.8, 12.0, 1.1, color=orange_edge)

    # Labels for flow
    ax.text(3.0, 8.35, "raw PDFs", fontsize=7, color="#666", style="italic")
    ax.text(6.2, 8.35, "paragraphs", fontsize=7, color="#666", style="italic")
    ax.text(3.0, 6.65, "NL question", fontsize=7, color="#666", style="italic")
    ax.text(6.2, 6.65, "candidates", fontsize=7, color="#666", style="italic")
    ax.text(8.2, 5.3, "confidence\nscore", fontsize=7, color="#666", style="italic")
    ax.text(9.5, 4.8, "below\nthreshold", fontsize=7, color=red_edge, style="italic")
    ax.text(8.2, 3.5, "above\nthreshold", fontsize=7, color=green_edge, style="italic")

    # No baked-in title; the markdown caption supplies the figure title in the report.
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
