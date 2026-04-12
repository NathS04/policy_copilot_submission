"""Apply Leeds template heading hierarchy and styling to the rendered docx.

Pandoc renders our markdown with one-too-deep heading levels relative to
the Leeds COMP3931 template convention:
  template: H1 = chapter, H2 = section, H3 = subsection, H4 = sub-subsection
  pandoc:   H1 = report title, H2 = chapter, H3 = section, H4 = subsection

This script:
  1. Enforces Leeds spec: 11pt body, 1.5 line spacing, 2.5cm margins.
  2. Tightens heading spacing to fit the 30-page body limit.
  3. Promotes every chapter heading to Heading 1.
  4. Promotes every X.Y section heading from Heading 3 to Heading 2.
  5. Promotes every X.Y.Z subsection heading from Heading 4 to Heading 3.
  6. Centres the title-page block.
  7. Adds page breaks before each chapter (Heading 1).
  8. Inserts all 10 figure images before their italic captions
     (pandoc does not embed raw <img> HTML tags).
  9. Italicises figure captions and centres them.
 10. Centres tables and applies clean grid styling.
 11. Restyles the manual TOC, List of Figures, and List of Tables bullet lists
     into clean indented entries with right-aligned dot-leader tab stops and
     page numbers (when scripts/build_report.py runs the second pass and a
     pagemap.json is found alongside this script).
"""
import json
import re
import sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, Emu, Inches, RGBColor
from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy

REPORT = Path(__file__).resolve().parent.parent / "docs" / "report"
# Pandoc renders the intermediate docx; this script post-processes it in place.
SRC = REPORT / "Final_Report_Draft_template.docx"
DST = REPORT / "Final_Report_Draft_template.docx"
# Optional page-number map written by build_report.py after the first PDF pass.
PAGEMAP_PATH = REPORT / "pagemap.json"
# Final PDF is rendered from the docx into the canonical primary path
# Final_Report_Draft.pdf (no separate _template.pdf duplicate).


# Patterns that should be Heading 1 (chapter-level).
# Both colon and no-colon forms are matched so the script keeps working
# whether the markdown uses "Chapter 1: Introduction..." or the Leeds-template
# "Chapter 1 Introduction..." form.
H1_PATTERNS = [
    r"^Chapter \d+[:\s]",
    r"^Appendix [AB][:\s]",
    r"^List of References$",
    r"^Summary$",
    r"^Acknowledgements$",
    r"^Declaration$",
    r"^Deliverables$",
    r"^Table of Contents$",
    r"^List of Figures$",
    r"^List of Tables$",
]

# Patterns for section level (X.Y - currently Heading 3, should be Heading 2)
H2_PATTERN = re.compile(r"^(?:\d+\.\d+|[AB]\.\d+|B\.\d+)\s+\S")

# Patterns for subsection level (X.Y.Z - currently Heading 4, should be Heading 3)
H3_PATTERN = re.compile(r"^(?:\d+\.\d+\.\d+|[AB]\.\d+\.\d+)\s+\S")

# Patterns for the main report title (should become Title style)
TITLE_TEXT = "Audit-Ready Policy Copilot"


def matches_h1(text: str) -> bool:
    return any(re.match(p, text) for p in H1_PATTERNS)


def add_page_break_before(paragraph):
    """Insert a page break before the given paragraph by adding pageBreakBefore property."""
    pPr = paragraph._element.get_or_add_pPr()
    pageBreakBefore = OxmlElement("w:pageBreakBefore")
    pPr.append(pageBreakBefore)


def split_sections_for_page_numbering(doc, chapter_one_paragraph):
    """
    Configure two sections for proper Leeds page numbering:
    - Section 1 (preliminaries, before Ch 1): lower-roman numerals
    - Section 2 (body + refs + appendices, from Ch 1): decimal (Arabic) restarting at 1

    This works by:
    1. Inserting a section break (sectPr) inside the LAST paragraph BEFORE
       Chapter 1, configured for Roman numerals (this defines Section 1).
    2. Setting the document-level body sectPr to Arabic restart-at-1
       (this defines Section 2 = everything after the section break).
    """
    # Find the paragraph immediately before Chapter 1 by XML element identity
    body_xml = doc.element.body
    paras = list(doc.paragraphs)
    ch1_idx = None
    target_elem = chapter_one_paragraph._element
    for i, p in enumerate(paras):
        if p._element is target_elem:
            ch1_idx = i
            break
    if ch1_idx is None or ch1_idx == 0:
        return False
    last_prelim = paras[ch1_idx - 1]

    # Bind the same default header (PAGE field) the Leeds template uses
    # for the body section to the preliminaries section too. Without this
    # binding the preliminary pages render with no page number at all,
    # violating the Leeds spec ("preliminaries from Summary to Table of
    # Contents should be sequentially numbered in Roman numerals").
    body_header_rid = None
    body_sectPr_existing = body_xml.find(qn("w:sectPr"))
    if body_sectPr_existing is not None:
        existing_ref = body_sectPr_existing.find(qn("w:headerReference"))
        if existing_ref is not None:
            body_header_rid = existing_ref.get(qn("r:id"))

    # Build sectPr for section 1 (preliminaries: lower roman)
    sect1 = OxmlElement("w:sectPr")
    if body_header_rid:
        headerRef = OxmlElement("w:headerReference")
        headerRef.set(qn("w:type"), "default")
        headerRef.set(qn("r:id"), body_header_rid)
        sect1.append(headerRef)
    pgSz1 = OxmlElement("w:pgSz")
    pgSz1.set(qn("w:w"), "11906")
    pgSz1.set(qn("w:h"), "16838")
    sect1.append(pgSz1)
    pgMar1 = OxmlElement("w:pgMar")
    for k, v in [("top", "1417"), ("right", "1417"), ("bottom", "1417"),
                 ("left", "1417"), ("header", "708"), ("footer", "708"), ("gutter", "0")]:
        pgMar1.set(qn(f"w:{k}"), v)
    sect1.append(pgMar1)
    pgNumType1 = OxmlElement("w:pgNumType")
    pgNumType1.set(qn("w:fmt"), "lowerRoman")
    pgNumType1.set(qn("w:start"), "1")
    sect1.append(pgNumType1)
    sect1Type = OxmlElement("w:type")
    sect1Type.set(qn("w:val"), "nextPage")
    sect1.append(sect1Type)

    # Attach sect1 sectPr to the last prelim paragraph
    pPr = last_prelim._element.get_or_add_pPr()
    pPr.append(sect1)

    # Now configure document body sectPr for section 2 (Arabic restart)
    body_sectPr = body_xml.find(qn("w:sectPr"))
    if body_sectPr is None:
        body_sectPr = OxmlElement("w:sectPr")
        body_xml.append(body_sectPr)
    # Remove existing pgNumType in body sectPr
    for e in body_sectPr.findall(qn("w:pgNumType")):
        body_sectPr.remove(e)
    # Add Arabic restart-at-1
    pgNumType2 = OxmlElement("w:pgNumType")
    pgNumType2.set(qn("w:fmt"), "decimal")
    pgNumType2.set(qn("w:start"), "1")
    body_sectPr.append(pgNumType2)

    return True


# Figure caption text -> (image filename, width in inches) mapping
# Caption matched by case-insensitive prefix to handle minor edits
FIGURE_MAP = [
    # (caption prefix, image filename, width in inches) - tightened to stay within 30-page body limit
    ("Figure 1.1: PRISMA", "fig_prisma.png", 3.5),
    ("Figure 2.0: Gantt chart", "fig_gantt.png", 4.5),
    ("Figure 2.1: End-to-end pipeline", "fig_data_flow.png", 4.5),
    ("Figure 4.1: Grouped bar chart", "fig_baselines.png", 4.0),
    ("Figure 4.2: Retrieval quality", "fig_retrieval.png", 4.0),
    ("Figure 4.3: Groundedness", "fig_groundedness.png", 4.0),
    ("Figure 4.4: Coverage", "fig_tradeoff.png", 3.5),
    ("Figure B.1: Answerable query result", "screenshot_answerable_query.png", 5.0),
    ("Figure B.2: Unanswerable query showing", "screenshot_unanswerable_query.png", 5.0),
    ("Figure B.3: Contradiction query showing", "screenshot_contradiction_query.png", 5.0),
]


def insert_figures_before_captions(doc, figures_dir):
    """For each italic figure caption, insert the corresponding image
    as a centered paragraph immediately before it. Strip surrounding
    empty paragraphs that pandoc inserted from div-block boundaries
    to keep the figure tightly attached to its caption."""
    inserted = 0
    skipped = 0
    seen = set()

    body = doc.element.body

    for p in list(doc.paragraphs):
        text = p.text.strip()
        if not text or not text.startswith("Figure"):
            continue
        matched = None
        for prefix, fname, width in FIGURE_MAP:
            if text.startswith(prefix) and prefix not in seen:
                matched = (fname, width)
                seen.add(prefix)
                break
        if not matched:
            continue
        fname, width = matched
        img_path = figures_dir / fname
        if not img_path.exists():
            print(f"  WARNING: image not found: {img_path}")
            skipped += 1
            continue

        # Remove empty paragraphs immediately before this caption
        cap_elem = p._element
        prev = cap_elem.getprevious()
        removed = 0
        while prev is not None and prev.tag.endswith("}p"):
            prev_text = "".join(prev.itertext()).strip()
            # Don't remove if it has substantive text or contains an image
            if prev_text or prev.findall(".//" + qn("w:drawing")):
                break
            to_remove = prev
            prev = prev.getprevious()
            body.remove(to_remove)
            removed += 1

        # Insert a new paragraph BEFORE this caption with the image
        new_p = p.insert_paragraph_before("")
        new_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        # Tighten spacing on image paragraph
        new_p.paragraph_format.space_before = Pt(2)
        new_p.paragraph_format.space_after = Pt(0)
        run = new_p.add_run()
        try:
            run.add_picture(str(img_path), width=Inches(width))
            inserted += 1
        except Exception as e:
            print(f"  WARNING: failed to insert {fname}: {e}")
            skipped += 1

        # Style the caption: italic + centered + smaller, tight spacing
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        for run in p.runs:
            run.font.italic = True
            run.font.size = Pt(10)

    print(f"Inserted {inserted} figure images, skipped {skipped}")


def style_tables(doc):
    """Apply consistent professional styling to all tables: centred,
    visible grid borders, shaded header row, consistent 10pt body text.

    Critical: every cell paragraph must use the Normal style (not the
    pandoc-emitted Compact, which the Leeds template does not define).
    """
    normal_style = doc.styles["Normal"]
    for table in doc.tables:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        try:
            table.style = "TableGrid"
        except KeyError:
            try:
                table.style = "Table Grid"
            except KeyError:
                pass

        # Wide tables (4+ columns) get autofit + smaller cells so long
        # identifiers like test_reproduce_online_preflight.py do not split
        # mid-word. 6+ columns drops to 8pt to stop multi-line wraps in tables
        # like B.8 Comparative Analysis.
        n_cols = len(table.columns) if table.columns else 0
        is_wide = n_cols >= 4
        if n_cols >= 6:
            cell_pt = 8
        elif is_wide:
            cell_pt = 9
        else:
            cell_pt = 10

        # Force visible single-line borders on every side and inside the table,
        # so the grid renders even if the table style lookup is unreliable.
        tblPr = table._element.find(qn("w:tblPr"))
        if tblPr is None:
            tblPr = OxmlElement("w:tblPr")
            table._element.insert(0, tblPr)
        existing_borders = tblPr.find(qn("w:tblBorders"))
        if existing_borders is not None:
            tblPr.remove(existing_borders)
        tblBorders = OxmlElement("w:tblBorders")
        # Outer box + horizontal row separators only; inner vertical lines
        # are intentionally omitted so the tables read as professional
        # academic black-and-grey rather than a busy spreadsheet grid.
        for side in ("top", "left", "bottom", "right", "insideH"):
            b = OxmlElement(f"w:{side}")
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), "4")
            b.set(qn("w:space"), "0")
            b.set(qn("w:color"), "auto")
            tblBorders.append(b)
        # Explicitly suppress inner vertical borders so the table style
        # cannot reintroduce them via inheritance.
        b_iv = OxmlElement("w:insideV")
        b_iv.set(qn("w:val"), "nil")
        tblBorders.append(b_iv)
        tblPr.append(tblBorders)

        for row_idx, row in enumerate(table.rows):
            is_header = row_idx == 0
            for cell in row.cells:
                tcPr = cell._element.get_or_add_tcPr()
                if is_header:
                    shd = OxmlElement("w:shd")
                    shd.set(qn("w:val"), "clear")
                    shd.set(qn("w:color"), "auto")
                    # Light grey (Word "Grey-15%") for a neutral, professional
                    # header band -- replaces the previous dark navy 2C3E50.
                    shd.set(qn("w:fill"), "D9D9D9")
                    tcPr.append(shd)
                tcMar = OxmlElement("w:tcMar")
                for side, val in [("top", "60"), ("bottom", "60"), ("left", "100"), ("right", "100")]:
                    mar = OxmlElement(f"w:{side}")
                    mar.set(qn("w:w"), val)
                    mar.set(qn("w:type"), "dxa")
                    tcMar.append(mar)
                tcPr.append(tcMar)
                for para in cell.paragraphs:
                    # Force Normal style so the paragraph is renderable.
                    para.style = normal_style
                    # Insert a zero-width space (U+200B) after every '_' in
                    # snake_case identifiers so LibreOffice can wrap long
                    # filenames such as test_reproduce_online_preflight.py
                    # without splitting them mid-word as
                    # `test_generation_schema. / py`.
                    for run in para.runs:
                        if run.text and "_" in run.text and "." in run.text:
                            run.text = run.text.replace("_", "_\u200b")
                    pf = para.paragraph_format
                    pf.line_spacing = 1.15
                    pf.space_before = Pt(0)
                    pf.space_after = Pt(0)
                    for run in para.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(cell_pt)
                        # Always black text; header is differentiated by the
                        # light-grey shading + bold, not by an inverted
                        # white-on-blue colour scheme.
                        run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
                        if is_header:
                            run.font.bold = True

        # For wide tables, switch the table layout from fixed to autofit and
        # clear pandoc-supplied per-column widths so LibreOffice / Word will
        # flex columns around the longest content (no more truncating
        # identifiers like `test_generation_schema.py` mid-word).
        if is_wide:
            tbl_layout = tblPr.find(qn("w:tblLayout"))
            if tbl_layout is None:
                tbl_layout = OxmlElement("w:tblLayout")
                tblPr.append(tbl_layout)
            tbl_layout.set(qn("w:type"), "autofit")
            tbl_w = tblPr.find(qn("w:tblW"))
            if tbl_w is None:
                tbl_w = OxmlElement("w:tblW")
                tblPr.append(tbl_w)
            tbl_w.set(qn("w:type"), "pct")
            tbl_w.set(qn("w:w"), "5000")
            tbl_grid = table._element.find(qn("w:tblGrid"))
            if tbl_grid is not None:
                for col in tbl_grid.findall(qn("w:gridCol")):
                    col.set(qn("w:w"), "0")
            for row in table.rows:
                for cell in row.cells:
                    tcPr = cell._element.find(qn("w:tcPr"))
                    if tcPr is not None:
                        tcW = tcPr.find(qn("w:tcW"))
                        if tcW is not None:
                            tcW.set(qn("w:w"), "0")
                            tcW.set(qn("w:type"), "auto")


def style_table_captions(doc):
    """Bold and slightly larger 'Table N.N:' captions; left-aligned."""
    for p in doc.paragraphs:
        text = p.text.strip()
        if re.match(r"^Table \d+\.\d+:", text) or re.match(r"^Table \d+\.\d+a?:", text):
            for run in p.runs:
                run.font.bold = True
                run.font.size = Pt(10.5)


def enforce_leeds_spec(doc):
    """Enforce Leeds spec: 11pt body, 1.5 line spacing, 2.5cm margins, tight headings."""
    # Margins: 2.5cm
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # Normal body: 11pt, 1.5 line spacing (Leeds spec), 4pt after for visible
    # paragraph separation. Leeds template's own Normal uses 6pt after, but
    # we use 4pt as a compromise to keep the body within the 30-page hard
    # limit set by COMP3931 layout requirements.
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11)
    normal.font.name = "Times New Roman"
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.space_before = Pt(0)
    pf.space_after = Pt(4)
    pf.widow_control = True

    # Compact and List Paragraph styles inherit from Normal but Pandoc emits
    # tighter defaults; align them with Normal so list items and table cells
    # do not visually clash with body paragraphs around them.
    for sname in ["Compact", "List Paragraph"]:
        try:
            cs = doc.styles[sname]
            cs.font.size = Pt(11)
            cspf = cs.paragraph_format
            cspf.line_spacing = 1.5
            cspf.space_before = Pt(0)
            cspf.space_after = Pt(2)
        except (KeyError, AttributeError):
            pass

    # Code blocks: monospace 9pt with light grey background, tight spacing.
    # Pandoc emits "Source Code" for fenced blocks and "Verbatim Char" for inline
    # code spans; the Leeds template does not pre-define either, so we set both.
    for sname in ["Source Code", "Verbatim Char", "Code"]:
        try:
            cs = doc.styles[sname]
            cs.font.size = Pt(9)
            cs.font.name = "Courier New"
            try:
                rpr = cs.element.get_or_add_rPr()
                rfonts = rpr.find(qn("w:rFonts"))
                if rfonts is None:
                    rfonts = OxmlElement("w:rFonts")
                    rpr.append(rfonts)
                for attr in ("ascii", "hAnsi", "cs"):
                    rfonts.set(qn(f"w:{attr}"), "Courier New")
            except Exception:
                pass
            cs.paragraph_format.line_spacing = 1.1
            cs.paragraph_format.space_before = Pt(2)
            cs.paragraph_format.space_after = Pt(2)
        except (KeyError, AttributeError):
            pass

    # Belt-and-braces: walk the body and force monospace on any paragraph whose
    # style id looks like a Pandoc code style, in case the style lookups above
    # missed a name. This catches inline `code` spans that pandoc tags as
    # "VerbatimChar" without a space.
    body = doc.element.body
    for p in body.iter(qn("w:p")):
        pStyle = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
        if pStyle is not None:
            sid = pStyle.get(qn("w:val")) or ""
            if "Source" in sid or "Verbatim" in sid or sid == "Code":
                for r in p.iter(qn("w:r")):
                    rpr = r.find(qn("w:rPr"))
                    if rpr is None:
                        rpr = OxmlElement("w:rPr")
                        r.insert(0, rpr)
                    rfonts = rpr.find(qn("w:rFonts"))
                    if rfonts is None:
                        rfonts = OxmlElement("w:rFonts")
                        rpr.append(rfonts)
                    for attr in ("ascii", "hAnsi", "cs"):
                        rfonts.set(qn(f"w:{attr}"), "Courier New")
                    sz = rpr.find(qn("w:sz"))
                    if sz is None:
                        sz = OxmlElement("w:sz")
                        rpr.append(sz)
                    sz.set(qn("w:val"), "18")  # 9pt = 18 half-points

    # Heading 1: chapter level — 15pt, tight
    # The Leeds template's Heading 1 has built-in pageBreakBefore which
    # forces every chapter to a new page. We strip that here so chapters
    # 2-5 flow continuously, saving body-page budget.
    h1 = doc.styles["Heading 1"]
    h1.font.size = Pt(15)
    h1.font.bold = True
    h1pf = h1.paragraph_format
    h1pf.space_before = Pt(8)
    h1pf.space_after = Pt(4)
    h1pf.line_spacing = 1.15
    h1pf.keep_with_next = True
    # Remove built-in pageBreakBefore from the H1 style itself
    h1_pPr = h1.element.find(qn("w:pPr"))
    if h1_pPr is not None:
        for el in h1_pPr.findall(qn("w:pageBreakBefore")):
            h1_pPr.remove(el)

    # Heading 2: section — 12pt, tight
    h2 = doc.styles["Heading 2"]
    h2.font.size = Pt(12)
    h2.font.bold = True
    h2pf = h2.paragraph_format
    h2pf.space_before = Pt(4)
    h2pf.space_after = Pt(2)
    h2pf.line_spacing = 1.15
    h2pf.keep_with_next = True

    # Heading 3: subsection — 11pt bold
    h3 = doc.styles["Heading 3"]
    h3.font.size = Pt(11)
    h3.font.bold = True
    h3pf = h3.paragraph_format
    h3pf.space_before = Pt(3)
    h3pf.space_after = Pt(1)
    h3pf.line_spacing = 1.15
    h3pf.keep_with_next = True

    # Heading 4: sub-subsection — 11pt italic
    try:
        h4 = doc.styles["Heading 4"]
        h4.font.size = Pt(11)
        h4.font.bold = False
        h4.font.italic = True
        h4pf = h4.paragraph_format
        h4pf.space_before = Pt(2)
        h4pf.space_after = Pt(1)
        h4pf.line_spacing = 1.15
        h4pf.keep_with_next = True
    except KeyError:
        pass


def remove_consecutive_empty_paragraphs(doc):
    """Collapse runs of >1 consecutive empty paragraphs to a single one
    to recover wasted vertical space introduced by pandoc div boundaries."""
    body = doc.element.body
    removed = 0
    paras = list(doc.paragraphs)
    prev_empty = False
    for p in paras:
        text = "".join(p._element.itertext()).strip()
        has_image = bool(p._element.findall(".//" + qn("w:drawing")))
        is_empty = not text and not has_image
        if is_empty and prev_empty:
            try:
                body.remove(p._element)
                removed += 1
            except Exception:
                pass
        prev_empty = is_empty
    print(f"Removed {removed} duplicate empty paragraphs")


def strip_unknown_pstyles(doc):
    """Remove or remap pStyle references that the Leeds template does not define.

    Pandoc emits <w:pStyle w:val="Compact"/> on table-cell paragraphs, but the
    official Leeds template has no Compact style; LibreOffice then fails to
    render those paragraphs (cells appear empty). Same risk for any other
    pandoc-emitted style that isn't in the template.
    """
    available = {s.style_id for s in doc.styles}
    body = doc.element.body
    removed = 0
    for pStyle in body.iter(qn("w:pStyle")):
        val = pStyle.get(qn("w:val"))
        if val and val not in available:
            parent = pStyle.getparent()
            if parent is not None:
                parent.remove(pStyle)
                removed += 1
    print(f"Stripped {removed} unknown pStyle references")


def _load_pagemap():
    """Return {entry_text: page_number} from PAGEMAP_PATH, or {} if absent."""
    if not PAGEMAP_PATH.exists():
        return {}
    try:
        return json.loads(PAGEMAP_PATH.read_text())
    except Exception as exc:
        print(f"  WARNING: could not parse pagemap.json: {exc}")
        return {}


def _add_dot_leader_tab(paragraph, position_pt=435):
    """Add a right-aligned tab stop with dot leader at the given position
    (in points from the left margin). 435pt ~= 6 inches, comfortable for an
    A4 page with 2.5cm margins.
    """
    pPr = paragraph._element.get_or_add_pPr()
    tabs = pPr.find(qn("w:tabs"))
    if tabs is None:
        tabs = OxmlElement("w:tabs")
        pPr.append(tabs)
    # Drop any existing tab stops so the leader is the only one in play.
    for old in list(tabs.findall(qn("w:tab"))):
        tabs.remove(old)
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:leader"), "dot")
    # Position is in twentieths of a point (dxa).
    tab.set(qn("w:pos"), str(int(position_pt * 20)))
    tabs.append(tab)


def _append_page_number_run(paragraph, page_number, font_pt=11, bold=False):
    """Append `<tab><page>` to the paragraph as a styled run so the dot
    leader fills the gap and the number sits flush right.
    """
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    for attr in ("ascii", "hAnsi", "cs"):
        rfonts.set(qn(f"w:{attr}"), "Times New Roman")
    rpr.append(rfonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(font_pt * 2)))
    rpr.append(sz)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    rpr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "none")
    rpr.append(u)
    if bold:
        b = OxmlElement("w:b")
        rpr.append(b)
    r.append(rpr)
    tab = OxmlElement("w:tab")
    r.append(tab)
    t = OxmlElement("w:t")
    t.text = str(page_number)
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    paragraph._element.append(r)


def _restyle_link_runs(paragraph, font_pt=11, bold=False):
    """Force every run (including those inside w:hyperlink) to plain black
    Times New Roman with no underline, optionally bold.
    """
    for r in paragraph._element.iter(qn("w:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            r.insert(0, rpr)
        rstyle = rpr.find(qn("w:rStyle"))
        if rstyle is not None:
            rpr.remove(rstyle)
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        for attr in ("ascii", "hAnsi", "cs"):
            rfonts.set(qn(f"w:{attr}"), "Times New Roman")
        sz = rpr.find(qn("w:sz"))
        if sz is None:
            sz = OxmlElement("w:sz")
            rpr.append(sz)
        sz.set(qn("w:val"), str(int(font_pt * 2)))
        color = rpr.find(qn("w:color"))
        if color is None:
            color = OxmlElement("w:color")
            rpr.append(color)
        color.set(qn("w:val"), "000000")
        u = rpr.find(qn("w:u"))
        if u is None:
            u = OxmlElement("w:u")
            rpr.append(u)
        u.set(qn("w:val"), "none")
        if bold:
            b = rpr.find(qn("w:b"))
            if b is None:
                b = OxmlElement("w:b")
                rpr.append(b)


def style_manual_toc(doc, pagemap):
    """Convert the pandoc-rendered TOC bullet list into a clean indented TOC
    (no bullet markers, depth-based indentation, dot-leader tab stop, and
    page numbers when a pagemap is supplied).
    """
    paras = list(doc.paragraphs)
    toc_idx = None
    for i, p in enumerate(paras):
        if p.text.strip() == "Table of Contents":
            toc_idx = i
            break
    if toc_idx is None:
        print("  TOC heading not found")
        return False

    end_idx = len(paras)
    for j in range(toc_idx + 1, len(paras)):
        text = paras[j].text.strip()
        sname = paras[j].style.name if paras[j].style else ""
        if text and "Heading" in sname:
            end_idx = j
            break

    normal_style = doc.styles["Normal"]
    styled = 0
    matched_pages = 0
    for j in range(toc_idx + 1, end_idx):
        p = paras[j]
        text = p.text.strip()
        if not text:
            continue
        ilvl = 0
        pPr = p._element.find(qn("w:pPr"))
        if pPr is not None:
            numPr = pPr.find(qn("w:numPr"))
            if numPr is not None:
                ilvl_elem = numPr.find(qn("w:ilvl"))
                if ilvl_elem is not None:
                    try:
                        ilvl = int(ilvl_elem.get(qn("w:val")) or 0)
                    except (TypeError, ValueError):
                        ilvl = 0
        p.style = normal_style
        new_pPr = p._element.find(qn("w:pPr"))
        if new_pPr is not None:
            for tag in ("w:numPr", "w:pStyle"):
                el = new_pPr.find(qn(tag))
                if el is not None:
                    new_pPr.remove(el)
        indent_pts = 14 + ilvl * 18
        p.paragraph_format.left_indent = Pt(indent_pts)
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        is_top_chapter = ilvl == 0 and (
            text.startswith("Chapter ") or text.startswith("Appendix ")
        )
        _restyle_link_runs(p, font_pt=11, bold=is_top_chapter)
        # Dot-leader tab stop and page number injection.
        page = pagemap.get(text)
        if page is not None:
            _add_dot_leader_tab(p, position_pt=435 - indent_pts)
            _append_page_number_run(p, page, font_pt=11, bold=is_top_chapter)
            matched_pages += 1
        styled += 1
    print(f"Styled {styled} TOC entries ({matched_pages} with page numbers)")
    return True


def style_manual_loft(doc, heading_text, pagemap):
    """Same treatment as TOC but for List of Figures / List of Tables.
    Items are flat (no indent depth), each one has a dot-leader tab and page
    number when the pagemap supplies one.
    """
    paras = list(doc.paragraphs)
    head_idx = None
    for i, p in enumerate(paras):
        if p.text.strip() == heading_text:
            head_idx = i
            break
    if head_idx is None:
        print(f"  '{heading_text}' heading not found")
        return False

    end_idx = len(paras)
    for j in range(head_idx + 1, len(paras)):
        text = paras[j].text.strip()
        sname = paras[j].style.name if paras[j].style else ""
        if text and "Heading" in sname:
            end_idx = j
            break

    normal_style = doc.styles["Normal"]
    styled = 0
    matched_pages = 0
    for j in range(head_idx + 1, end_idx):
        p = paras[j]
        text = p.text.strip()
        if not text:
            continue
        p.style = normal_style
        new_pPr = p._element.find(qn("w:pPr"))
        if new_pPr is not None:
            for tag in ("w:numPr", "w:pStyle"):
                el = new_pPr.find(qn(tag))
                if el is not None:
                    new_pPr.remove(el)
        p.paragraph_format.left_indent = Pt(14)
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        _restyle_link_runs(p, font_pt=11, bold=False)
        page = pagemap.get(text)
        if page is not None:
            _add_dot_leader_tab(p, position_pt=421)
            _append_page_number_run(p, page, font_pt=11, bold=False)
            matched_pages += 1
        styled += 1
    print(f"Styled {styled} '{heading_text}' entries ({matched_pages} with page numbers)")
    return True


def insert_leeds_logo(doc, logo_path):
    """Insert the Leeds University logo at the very top of the document
    (above the title block), centred, on the title page."""
    if not logo_path.exists():
        print(f"  WARNING: Leeds logo not found at {logo_path}, skipping")
        return False
    body = doc.element.body
    first_para = doc.paragraphs[0]
    new_p = first_para.insert_paragraph_before("")
    new_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    new_p.paragraph_format.space_before = Pt(0)
    new_p.paragraph_format.space_after = Pt(12)
    run = new_p.add_run()
    try:
        run.add_picture(str(logo_path), width=Inches(2.6))
        return True
    except Exception as e:
        print(f"  WARNING: failed to insert Leeds logo: {e}")
        return False


def main() -> int:
    doc = Document(str(SRC))
    strip_unknown_pstyles(doc)
    enforce_leeds_spec(doc)
    logo_path = REPORT / "figures" / "leeds_logo.jpeg"
    logo_inserted = insert_leeds_logo(doc, logo_path)
    print(f"Leeds logo inserted: {logo_inserted}")

    # Insert figure images before each italic caption
    figures_dir = REPORT / "figures"
    insert_figures_before_captions(doc, figures_dir)

    # Restyle the pandoc-rendered TOC, List of Figures, and List of Tables
    # bullet lists as clean indented entries with dot-leader tab stops.
    # Page numbers are injected if pagemap.json is present (second pass).
    pagemap = _load_pagemap()
    if pagemap:
        print(f"Loaded pagemap with {len(pagemap)} entries")
    else:
        print("No pagemap.json found; running pass 1 (no page numbers)")
    style_manual_toc(doc, pagemap)
    style_manual_loft(doc, "List of Figures", pagemap)
    style_manual_loft(doc, "List of Tables", pagemap)

    # Style tables and table captions
    style_tables(doc)
    style_table_captions(doc)

    # Remove duplicate consecutive empty paragraphs
    remove_consecutive_empty_paragraphs(doc)

    promoted_h1 = 0
    promoted_h2 = 0
    promoted_h3 = 0
    title_demoted = False
    seen_declaration = False
    chapter_one_para = None

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        current_style = p.style.name if p.style else ""

        if text == "Declaration":
            seen_declaration = True

        # Demote the main report title from Heading 1 to Normal so it doesn't
        # force a page break and sits on the title page with everything else.
        if text == TITLE_TEXT and not title_demoted:
            p.style = doc.styles["Normal"]
            # Make it big and bold via direct run formatting
            for run in p.runs:
                run.font.size = Pt(22)
                run.font.bold = True
            title_demoted = True
            continue

        # Demote the subtitle (currently Heading 2) to Normal too
        if not seen_declaration and "Heading 2" in current_style:
            # If this is the subtitle (Evidence-Grounded...) demote it
            if text.startswith("Evidence-Grounded"):
                p.style = doc.styles["Normal"]
                for run in p.runs:
                    run.font.size = Pt(14)
                    run.font.italic = True
                continue

        # Promote H2 -> H1 for chapter-level headings (only after Declaration)
        if "Heading 2" in current_style and matches_h1(text):
            p.style = doc.styles["Heading 1"]
            # Force a page break for major front-matter, References, and Appendices.
            # Chapters 2-5 flow continuously (we strip H1 style page-break-before
            # in enforce_leeds_spec) to stay within the 30-page body limit.
            wants_page_break = (
                text == "Declaration"
                or text == "Deliverables"
                or text == "Summary"
                or text == "Acknowledgements"
                or text == "Table of Contents"
                or text == "List of Figures"
                or text == "List of Tables"
                or text.startswith("Chapter 1")
                or text == "List of References"
                or text.startswith("Appendix ")
            )
            if wants_page_break:
                add_page_break_before(p)
            if text.startswith("Chapter 1") and chapter_one_para is None:
                chapter_one_para = p
            promoted_h1 += 1
            continue

        # Promote H3 -> H2 for X.Y section headings
        if "Heading 3" in current_style and H2_PATTERN.match(text):
            p.style = doc.styles["Heading 2"]
            promoted_h2 += 1
            continue

        # Promote H4 -> H3 for X.Y.Z subsection headings
        if "Heading 4" in current_style and H3_PATTERN.match(text):
            p.style = doc.styles["Heading 3"]
            promoted_h3 += 1
            continue

    # Centre the title-page elements (everything before "Declaration")
    for p in doc.paragraphs:
        if p.text.strip() == "Declaration":
            break
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Insert section break for Roman -> Arabic page numbering
    section_split = False
    if chapter_one_para is not None:
        section_split = split_sections_for_page_numbering(doc, chapter_one_para)

    doc.save(str(DST))
    print(f"Promoted {promoted_h1} headings to Heading 1 (chapter level)")
    print(f"Promoted {promoted_h2} headings to Heading 2 (section level)")
    print(f"Promoted {promoted_h3} headings to Heading 3 (subsection level)")
    print(f"Title demoted to Normal: {title_demoted}")
    print(f"Section split for page numbering: {section_split}")
    print(f"Wrote: {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
