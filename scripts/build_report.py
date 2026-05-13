"""Two-pass build of the dissertation PDF.

Pass 1:
  pandoc -> docx (raw)
  apply_leeds_template.py (no pagemap) -> docx (styled, no page numbers)
  LibreOffice headless -> PDF (intermediate)

Then we read the intermediate PDF, build a {entry_text -> page_number} map
covering every TOC/LoF/LoT entry, and write it to docs/report/pagemap.json.

Pass 2:
  pandoc -> docx (raw, regenerated)
  apply_leeds_template.py (loads pagemap.json) -> docx (styled WITH numbers)
  LibreOffice headless -> PDF (final)

The two-pass design avoids relying on LibreOffice headless to refresh Word
TOC/PAGEREF fields, which has been observed to fail intermittently. Real
extracted page numbers are typeset directly into the docx instead.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "report"
REPORT_STEM = "Final_Report_Nathaniel_Sebastian_201715051"
SRC_MD = REPORT / f"{REPORT_STEM}.md"
DOCX = REPORT / "build_assets" / "Final_Report_Template.docx"
PDF = REPORT / f"{REPORT_STEM}.pdf"
PAGEMAP = REPORT / "pagemap.json"
TEMPLATE = REPORT / "build_assets" / "Final_Report_Template.docx"

PANDOC = "pandoc"
SOFFICE = "/opt/homebrew/bin/soffice"


def run(cmd, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"Command failed: {cmd[0]}")
    if result.stdout.strip():
        # Trim noisy converter chatter; keep only first 8 lines.
        lines = result.stdout.strip().splitlines()
        for line in lines[:8]:
            print(f"    {line}")
    return result


def render_docx():
    print("[pandoc] markdown -> docx")
    cmd = [
        PANDOC,
        str(SRC_MD),
        "-f", "markdown+raw_html+native_divs",
        "-t", "docx",
        f"--reference-doc={TEMPLATE}",
        "-o", str(DOCX),
    ]
    run(cmd, cwd=REPORT)


def apply_template():
    print("[apply_leeds_template]")
    run([sys.executable, str(ROOT / "scripts" / "apply_leeds_template.py")])


def render_pdf():
    print("[soffice] docx -> pdf")
    cmd = [
        SOFFICE,
        "--headless",
        "--norestore",
        "--nologo",
        "--nofirststartwizard",
        "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", str(REPORT),
        str(DOCX),
    ]
    run(cmd, timeout=180)
    # soffice writes <DOCX-stem>.pdf into --outdir; rename to canonical PDF.
    template_pdf = REPORT / (DOCX.stem + ".pdf")
    if template_pdf.exists():
        template_pdf.replace(PDF)


def to_roman(n: int) -> str:
    vals = [
        (1000, "m"), (900, "cm"), (500, "d"), (400, "cd"),
        (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
        (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i"),
    ]
    out = []
    for v, s in vals:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def build_pagemap_from_pdf(pdf_path: Path, entries: list[str]) -> dict:
    """For each entry text, find the page it appears on. Page numbers are
    expressed in the visible numbering scheme (Roman for preliminaries,
    Arabic restarting at 1 from Chapter 1), mirroring the section-break
    setup in apply_leeds_template.

    Two sources are combined:
      1. Pandoc-generated PDF outline bookmarks (heading text -> page).
         These cover all chapter, section, and subsection headings.
      2. Per-page text search for figure / table captions, which are not
         in the outline.
    """
    import pypdf

    reader = pypdf.PdfReader(str(pdf_path))
    n_pages = len(reader.pages)

    # 1) Walk the PDF outline. Map outline title -> absolute (0-indexed) page.
    outline_pages: dict[str, int] = {}

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                try:
                    page_num = reader.get_destination_page_number(it)
                except Exception:
                    page_num = None
                if page_num is not None:
                    title = (it.title or "").strip()
                    if title and title not in outline_pages:
                        outline_pages[title] = page_num

    try:
        walk(reader.outline)
    except Exception as exc:
        print(f"  WARNING: could not walk outline: {exc}")

    # 2) Scan page text for figure / table captions.
    pages_text: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages_text.append(re.sub(r"\s+", " ", text).strip())

    # Find the absolute page where Chapter 1 begins (from the outline).
    chapter_one_abs = outline_pages.get(
        "Chapter 1 Introduction and Background Research"
    )

    def to_visible_page(abs_page: int) -> str | int:
        if chapter_one_abs is None:
            return abs_page + 1
        if abs_page < chapter_one_abs:
            return to_roman(abs_page + 1)
        return (abs_page - chapter_one_abs) + 1

    pagemap: dict[str, str | int] = {}
    for entry in entries:
        # Try the outline first (heading entries match exactly).
        if entry in outline_pages:
            pagemap[entry] = to_visible_page(outline_pages[entry])
            continue

        # Figure / table entries — search PDF text after the front matter
        # to skip TOC / List of Figures / List of Tables instances. We
        # start scanning from Chapter 1 onwards.
        #
        # Two-stage match (most-specific first):
        #   1. The exact descriptor text from the LoF/LoT entry, e.g.
        #      "Figure B.1: Answerable query result showing extractive
        #       fallback with citations". This matches the italic caption
        #       under the figure and ignores any earlier paragraph that
        #       happens to begin "Figure B.1: Answerable query." (the
        #       in-text introduction sentence used in Appendix B.7.3).
        #   2. The bare label "Figure B.1:" / "Table 4.3:" as a fallback
        #      for figures/tables whose body caption shortens or rephrases
        #      the LoF descriptor.
        m_fig = re.match(r"^(Figure (?:\d+\.\d+|B\.\d+))\s+(.*)$", entry)
        m_tbl = re.match(r"^(Table (?:\d+\.\d+|B\.\d+))\s+(.*)$", entry)
        if m_fig:
            num = m_fig.group(1)
            descriptor = m_fig.group(2).strip().rstrip(".")
        elif m_tbl:
            num = m_tbl.group(1)
            descriptor = m_tbl.group(2).strip().rstrip(".")
        else:
            print(f"  WARNING: no outline entry and not a figure/table: '{entry}'")
            continue

        full_label = f"{num}: {descriptor}"     # specific
        bare_label = f"{num}:"                  # generic fallback

        search_start = chapter_one_abs if chapter_one_abs is not None else 0
        found_abs = None
        # Pass 1: specific match against the full caption descriptor.
        # Compare on whitespace-collapsed text so soft-hyphenation / line
        # wrapping in the rendered PDF does not break the substring search.
        normalised_full = re.sub(r"\s+", " ", full_label).lower()
        for i in range(search_start, n_pages):
            page_norm = re.sub(r"\s+", " ", pages_text[i]).lower()
            if normalised_full in page_norm:
                found_abs = i
                break
        # Pass 2: bare-label fallback if the descriptor never matches.
        if found_abs is None:
            for i in range(search_start, n_pages):
                if bare_label in pages_text[i]:
                    found_abs = i
                    break
        if found_abs is None:
            print(f"  WARNING: no page found for '{entry}'")
            continue
        pagemap[entry] = to_visible_page(found_abs)

    return pagemap


def collect_entries_from_markdown() -> list[str]:
    """Extract every TOC, LoF, LoT entry text from the markdown so we can
    look up matching page numbers. This intentionally re-derives the list
    from the source rather than trusting the docx, so it stays in sync if
    the markdown is edited."""
    entries: list[str] = []
    text = SRC_MD.read_text()

    # TOC items: bullet list under "## Table of Contents" until next "##" heading.
    toc_match = re.search(
        r"## Table of Contents\n(.*?)(?=\n## )",
        text, re.DOTALL,
    )
    if toc_match:
        for line in toc_match.group(1).splitlines():
            m = re.match(r"^\s*-\s+\[([^\]]+)\]\([^)]+\)", line)
            if m:
                entries.append(m.group(1).strip())

    # List of Figures: bullet list under "## List of Figures".
    lof_match = re.search(
        r"## List of Figures\n(.*?)(?=\n## )",
        text, re.DOTALL,
    )
    if lof_match:
        for line in lof_match.group(1).splitlines():
            m = re.match(r"^\s*-\s+\[([^\]]+)\]\([^)]+\)", line)
            if m:
                entries.append(m.group(1).strip())

    # List of Tables: bullet list under "## List of Tables".
    lot_match = re.search(
        r"## List of Tables\n(.*?)(?=\n## |\n</div>)",
        text, re.DOTALL,
    )
    if lot_match:
        for line in lot_match.group(1).splitlines():
            m = re.match(r"^\s*-\s+\[([^\]]+)\]\([^)]+\)", line)
            if m:
                entries.append(m.group(1).strip())

    return entries


def main() -> int:
    if not SRC_MD.exists():
        raise SystemExit(f"Missing {SRC_MD}")
    if not TEMPLATE.exists():
        raise SystemExit(f"Missing {TEMPLATE}")

    # Clear stale pagemap so pass 1 produces a no-page-number TOC for the
    # intermediate PDF. (apply_leeds_template uses absence as the signal.)
    if PAGEMAP.exists():
        PAGEMAP.unlink()
        print(f"Removed stale {PAGEMAP.name}")

    print("\n=== PASS 1: build intermediate PDF (no page numbers in TOC) ===")
    render_docx()
    apply_template()
    render_pdf()

    print("\n=== build pagemap from intermediate PDF ===")
    entries = collect_entries_from_markdown()
    print(f"  {len(entries)} entries in TOC/LoF/LoT")
    pagemap = build_pagemap_from_pdf(PDF, entries)
    PAGEMAP.write_text(json.dumps(pagemap, indent=2, ensure_ascii=False))
    print(f"  wrote {len(pagemap)} mappings to {PAGEMAP.name}")

    # Iterate to convergence. Inserting page numbers into the TOC/LoF/LoT
    # may shift back-matter pagination by 1 page when long entries wrap or
    # extra rows push paragraphs onto a new page. Rebuild and re-extract
    # the pagemap until two consecutive maps agree, or up to MAX_PASSES.
    MAX_PASSES = 5
    prev_map = pagemap
    for pass_idx in range(2, MAX_PASSES + 1):
        print(f"\n=== PASS {pass_idx}: rebuild PDF with current pagemap ===")
        render_docx()
        apply_template()
        render_pdf()

        new_map = build_pagemap_from_pdf(PDF, entries)
        diffs = {
            k: (prev_map.get(k), new_map.get(k))
            for k in set(prev_map) | set(new_map)
            if prev_map.get(k) != new_map.get(k)
        }
        if not diffs:
            print(f"  pagemap converged after pass {pass_idx}")
            break
        print(f"  {len(diffs)} entries shifted; updating pagemap and rebuilding")
        for k, (old, new) in list(diffs.items())[:6]:
            print(f"    {k!r:55s}  {old!r} -> {new!r}")
        if len(diffs) > 6:
            print(f"    ... and {len(diffs)-6} more")
        PAGEMAP.write_text(json.dumps(new_map, indent=2, ensure_ascii=False))
        prev_map = new_map
    else:
        print(f"  WARNING: pagemap did not converge within {MAX_PASSES} passes")

    print("\n=== done ===")
    print(f"Final PDF: {PDF}")
    print(f"Final DOCX: {DOCX}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
