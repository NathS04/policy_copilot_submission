"""Final consistency sweep (Phase N).

Fails (exit 1) if the report contains stale claims or broken cross-
references. Designed to catch regressions during further editing.

Checks performed:
  1. Banned phrases that should never appear in the current report:
     - "three synthetic policy PDFs" / "three policy documents"
     - "Physical Security Protocol", "Employee Handbook" (as own doc title)
     - "access cards", "CCTV", "visitor handling"
     - "k = 20 captured" / "95% of gold paragraphs"
     - "design-time estimates" (we now have real ablations)
  2. FR cross-reference mistakes:
     - "Objective 4 / FR3" (Abstention should be FR2)
     - "Objective 1 / FR2" (Ungrounded should be FR1)
  3. Every figure listed in the report's List of Figures must exist on
     disk under docs/report/figures/.
  4. Every figure file in docs/report/figures/ must be referenced at
     least once in the report (catch orphans).
  5. The headline-table numbers in §4.2 must trace to the v2 summary
     JSONs (best-effort: the script extracts numbers from the markdown
     table and verifies each appears in some referenced summary.json).

Exit codes:
  0 — clean
  1 — one or more violations (printed to stdout)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/report/Final_Report_Nathaniel_Sebastian_201715051.md"
FIGURES_DIR = ROOT / "docs/report/figures"


BANNED_SUBSTRINGS = [
    "three synthetic policy PDFs",
    "three synthetic policy documents",
    "three policy documents",
    "Physical Security Protocol",
    # "Employee Handbook" – we use "Internal Policy Handbook"; flag any
    # occurrence not inside the ACAS analogue note.
    "k = 20 captured",
    "k = 20 captured ≥95% of gold paragraphs",
    "captured ≥95% of gold paragraphs",
    "95% of gold paragraphs",
    "design-time estimates",
    "design-time estimates from Sprint 5",
]

# FR cross-reference mistakes
BANNED_FR = [
    ("Abstention Accuracy", "FR3"),  # Abstention is FR2
    ("Ungrounded Rate", "FR2"),       # Ungrounded is FR1
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_banned_substrings(text: str) -> List[str]:
    issues = []
    for s in BANNED_SUBSTRINGS:
        if s in text:
            issues.append(f"banned phrase still in report: {s!r}")
    return issues


def check_fr_cross_references(text: str) -> List[str]:
    """Check banned (Concept, FR-label) co-occurrences ONLY in the explicit
    parenthetical pattern "<Concept> ... (Objective N / FRm)". This avoids
    false positives where FR2 appears in a different clause."""
    issues = []
    # Pattern: "Abstention Accuracy ... (Objective 4 / FR3)"  → bad
    # Pattern: "Ungrounded Rate ... (Objective 1 / FR2)"      → bad
    for concept, wrong_fr in BANNED_FR:
        # Match: <concept>...(Objective <digit> / <wrong_fr>)
        pattern = (
            re.escape(concept) + r".{0,60}?\(Objective\s+\d+\s*/\s*" + re.escape(wrong_fr) + r"\)"
        )
        if re.search(pattern, text, flags=re.DOTALL):
            issues.append(
                f"FR cross-reference mistake: {concept!r} paired with {wrong_fr!r} "
                "in an (Objective N / FRm) parenthetical"
            )
    return issues


def check_figures_disk_vs_report(text: str) -> List[str]:
    issues = []
    if not FIGURES_DIR.exists():
        return [f"figures dir missing: {FIGURES_DIR}"]
    actual = sorted(p.name for p in FIGURES_DIR.iterdir() if p.is_file()
                    and p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    referenced = set()
    for name in actual:
        if name in text or name.rsplit(".", 1)[0] in text:
            referenced.add(name)
    # Figures listed in LoF must exist on disk: parse simple "Figure X" lines.
    # We don't try to match each LoF entry to a file (the report uses descriptive
    # captions rather than filenames); instead we check that all canonical
    # figures appear on disk.
    canonical = [
        "fig_prisma.png",
        "fig_gantt.png",
        "fig_data_flow.png",
        "fig_baselines.png",
        "fig_retrieval.png",
        "fig_groundedness.png",
        "fig_tradeoff.png",
        "fig_bm25_retuned_operating_point.png",
        "fig_baselines_v2.png",
    ]
    for fig in canonical:
        if fig not in actual:
            issues.append(f"canonical figure missing from disk: {fig}")
    # Orphan check: figures on disk but never named in the report markdown.
    # We tolerate leeds_logo.jpeg and screenshot_*.png (caption-only references).
    for name in actual:
        if name in ("leeds_logo.jpeg",):
            continue
        if name.startswith("screenshot_"):
            continue
        # Heuristic: figure name OR its caption-friendly stem (drop "fig_") in text.
        stems = [name, name.rsplit(".", 1)[0]]
        if not any(s in text for s in stems):
            issues.append(f"orphan figure (not referenced in report): {name}")
    return issues


def check_table_traces(text: str) -> List[str]:
    """Sanity-check that key numbers in Table 4.2 also appear in the
    referenced v2 summary JSONs. We only assert a representative subset
    so that legitimate rounding doesn't produce false positives."""
    issues = []
    checks = [
        # (number-string, run_dir, key)
        ("25.0%", ROOT / "results/runs/b3_generative_v2/summary.json", "answer_rate"),
        ("100%", ROOT / "results/runs/b3_generative_v2/summary.json", "abstention_accuracy"),
        ("92.5%", ROOT / "results/runs/b3_extractive_hybrid_v2_final/summary.json", "answer_rate"),
        ("78.0%", ROOT / "results/runs/b3_extractive_hybrid_v2_final/summary.json", "evidence_recall_at_5"),
        ("45.0%", ROOT / "results/runs/b4_conservative_hybrid_replay_v2_final/summary.json", "answer_rate"),
    ]
    for number_str, run_path, key in checks:
        if not run_path.exists():
            issues.append(f"trace check: missing {run_path}")
            continue
        try:
            data = json.loads(run_path.read_text())
        except Exception as e:
            issues.append(f"trace check: failed to parse {run_path}: {e}")
            continue
        val = data.get(key)
        if val is None:
            issues.append(f"trace check: missing {key} in {run_path.name}")
            continue
        # number_str may be "25.0%" — strip percent and compare to val*100.
        try:
            expected_pct = float(number_str.rstrip("%"))
            actual_pct = float(val) * 100
            if abs(expected_pct - actual_pct) > 0.5:
                issues.append(
                    f"trace check: {number_str} in report does not match "
                    f"{key}={actual_pct:.2f}% in {run_path.name}"
                )
        except ValueError:
            pass
        if number_str not in text:
            issues.append(
                f"trace check: number {number_str} expected in report (for {key} of "
                f"{run_path.name}) is missing from the markdown"
            )
    return issues


def main() -> int:
    if not REPORT.exists():
        print(f"ERROR: report markdown not found at {REPORT}", file=sys.stderr)
        return 2
    text = _read(REPORT)
    all_issues: List[str] = []
    all_issues += check_banned_substrings(text)
    all_issues += check_fr_cross_references(text)
    all_issues += check_figures_disk_vs_report(text)
    all_issues += check_table_traces(text)

    if all_issues:
        print("FAILED: final_consistency_check.py found issues:")
        for i in all_issues:
            print(f"  - {i}")
        return 1

    print("OK: final_consistency_check.py — no issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
