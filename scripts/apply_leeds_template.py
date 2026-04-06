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
"""
import re
import sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, Emu
from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

REPORT = Path(__file__).resolve().parent.parent / "docs" / "report"
SRC = REPORT / "Final_Report_Draft_template.docx"
DST = REPORT / "Final_Report_Draft_template.docx"


# Patterns that should be Heading 1 (chapter-level)
H1_PATTERNS = [
    r"^Chapter \d+:",
    r"^Appendix [AB]:",
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

    # Build sectPr for section 1 (preliminaries: lower roman)
    sect1 = OxmlElement("w:sectPr")
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


def enforce_leeds_spec(doc):
    """Enforce Leeds spec: 11pt body, 1.5 line spacing, 2.5cm margins, tight headings."""
    # Margins: 2.5cm
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # Normal body: 11pt, 1.5 line spacing, tight paragraph spacing
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11)
    normal.font.name = "Times New Roman"
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)  # was 6
    pf.widow_control = True

    # Override common table-related styles to be compact (9pt, no extra spacing)
    table_style_names = ["Table Grid", "Table Normal", "Light Shading", "Light Grid", "Medium Shading 1"]
    for sname in table_style_names:
        try:
            ts = doc.styles[sname]
            ts.font.size = Pt(9)
            ts.paragraph_format.line_spacing = 1.0
            ts.paragraph_format.space_before = Pt(0)
            ts.paragraph_format.space_after = Pt(0)
        except (KeyError, AttributeError):
            pass

    # Compact body tables: every cell paragraph -> 9pt, single line spacing
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.line_spacing = 1.0
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.space_after = Pt(0)
                    for run in para.runs:
                        run.font.size = Pt(9)

    # Compact code blocks (Source Code style or similar)
    for sname in ["Source Code", "Verbatim Char", "Compact"]:
        try:
            cs = doc.styles[sname]
            cs.font.size = Pt(8.5)
            cs.paragraph_format.line_spacing = 1.0
            cs.paragraph_format.space_before = Pt(2)
            cs.paragraph_format.space_after = Pt(2)
        except (KeyError, AttributeError):
            pass

    # Heading 1: chapter level — 16pt, modest space-before (was 36pt!)
    h1 = doc.styles["Heading 1"]
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1pf = h1.paragraph_format
    h1pf.space_before = Pt(12)
    h1pf.space_after = Pt(8)
    h1pf.line_spacing = 1.15
    h1pf.keep_with_next = True

    # Heading 2: section — 13pt, tight
    h2 = doc.styles["Heading 2"]
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2pf = h2.paragraph_format
    h2pf.space_before = Pt(8)
    h2pf.space_after = Pt(4)
    h2pf.line_spacing = 1.15
    h2pf.keep_with_next = True

    # Heading 3: subsection — 11.5pt
    h3 = doc.styles["Heading 3"]
    h3.font.size = Pt(11.5)
    h3.font.bold = True
    h3pf = h3.paragraph_format
    h3pf.space_before = Pt(6)
    h3pf.space_after = Pt(3)
    h3pf.line_spacing = 1.15
    h3pf.keep_with_next = True

    # Heading 4: sub-subsection — 11pt italic
    try:
        h4 = doc.styles["Heading 4"]
        h4.font.size = Pt(11)
        h4.font.bold = False
        h4.font.italic = True
        h4pf = h4.paragraph_format
        h4pf.space_before = Pt(4)
        h4pf.space_after = Pt(2)
        h4pf.line_spacing = 1.15
        h4pf.keep_with_next = True
    except KeyError:
        pass


def main() -> int:
    doc = Document(str(SRC))
    enforce_leeds_spec(doc)
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
            # Track Chapter 1 for section break (Arabic restart)
            if text.startswith("Chapter 1:") and chapter_one_para is None:
                chapter_one_para = p
                add_page_break_before(p)
            elif text.startswith("Chapter ") or text.startswith("Appendix "):
                add_page_break_before(p)
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
