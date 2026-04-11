# Final Submission Checklist — Audit-Ready Policy Copilot

**Project:** University of Leeds COMP3931 Individual Project
**Title:** Audit-Ready Policy Copilot — Evidence-Grounded Retrieval-Augmented Generation with Deterministic Reliability Controls
**Author:** Nathaniel Sebastian (Student ID: 201715051)
**Module:** COMP3931 Individual Project
**Session:** 2025/26
**Finalised:** 30 April 2026

## Final artefacts

| Artefact | Path | Notes |
| --- | --- | --- |
| Final report (PDF) | `docs/report/Final_Report_Draft.pdf` | 55 pages total, A4, generated from markdown via two-pass build |
| Editable source (markdown) | `docs/report/Final_Report_Draft.md` | Single-file source; LoF / LoT / TOC are markdown lists post-processed by the build script |
| Intermediate DOCX | `docs/report/Final_Report_Draft_template.docx` | Pandoc + `apply_leeds_template.py` output, retained for reference |
| Build orchestrator | `scripts/build_report.py` | Two-pass build (pagemap then final render) |
| Template post-processor | `scripts/apply_leeds_template.py` | Heading promotion, table styling, TOC / LoF / LoT typography |
| Leeds template | `docs/report/leeds_template.docx` | Pandoc reference doc |

## PDF verification

| Metric | Value |
| --- | --- |
| Total PDF pages | 55 |
| First body page (Chapter 1) | absolute page 10 (body page 1) |
| Last body page (end of Chapter 5) | absolute page 37 (body page 28) |
| Body page count (Chapters 1–5) | **28 pages** (within the stated 30-page body limit) |
| Summary page count | 1 page (absolute page 4 / Roman iv) |
| Front-matter pages (i–ix) | 9 pages of Roman-numeral preliminaries |
| References + Appendices | absolute pages 38–55 (excluded from body limit per Deliverables wording) |
| File size | 1,436,834 bytes (~1.4 MB) |
| PDF link annotations | 69 total (66 internal navigation, 3 external URI) |
| External URIs in PDF | Deloitte AI Institute report, Pinecone tutorial, GitHub repository |

## Hyperlink verification

The PDF was inspected with `pypdf` to confirm link annotations exist:

```
total link annots: 69  internal(GoTo): 66  external URI: 3
```

Internal navigation covers every entry in the Table of Contents,
List of Figures, and List of Tables. External URIs cover the
GitHub repository link in Appendix B and the two web-hosted
references in the bibliography (Deloitte 2024, Kamradt 2024).
LibreOffice's PDF export embeds these as `/Link` annotations with
`/URI` actions, which all standard PDF viewers treat as clickable.

## Tests / report status

The codebase test suite (188 tests / 38 files) passes on the submitted
build, as recorded in §B.7.1. No tests were modified during the final
polish pass; all changes were to the report markdown, the build script,
and the post-processor script.

## Final checks completed

- [x] Title page reads "Nathaniel Sebastian" + "Student ID: 201715051"; no
  abbreviated author name remains in the source or the PDF text dump.
- [x] Declaration page has typed signature ("Nathaniel Sebastian") and date
  ("30 April 2026"); spacing is intentional, not accidental.
- [x] AI-usage wording is consistent across Acknowledgements,
  §A.3.4 Professional Standards, and Appendix B.5.
- [x] Table of Contents, List of Figures, and List of Tables render with
  dot leaders and real page numbers (in the visible numbering scheme:
  lower-roman for preliminaries, Arabic restarting at 1 from Chapter 1).
- [x] Appendix table renames applied: Table 1.1 → Table B.1, Table 3.2 →
  Table B.2, with §1.10 cross-reference updated.
- [x] Table 4.3 caption explicitly notes the BM25 fallback; Table 4.5
  caption explicitly notes the dev-phase ablation status with the
  final B3 reference row.
- [x] Environmental Impact paragraph (§A.3.3) and Ethics Q5 use the
  prescribed B1/B2 offline wording.
- [x] `pdfplumber` and `pypdf` references reconciled (pypdf is the active
  extraction path; pdfplumber is documented as an optional fallback).
- [x] Body length within the stated 30-page limit (28 pages).
- [x] Summary fits on one A4 page.
- [x] No placeholder or marker strings remain in the PDF (TODO, FIXME,
  XXX, broken cross-reference text, or the truncated-name placeholder
  that previously appeared on the title page).
- [x] Every figure has a caption directly beneath it; every table has a
  caption directly above it.
- [x] All wide tables (B.1, B.2, B.7.x) wrap snake_case identifiers via
  zero-width-space injection so no identifiers split mid-word.
- [x] Two-pass build is reproducible: `python scripts/build_report.py`
  regenerates `Final_Report_Draft.pdf` from the markdown source on a
  fresh clone with pandoc, LibreOffice, python-docx, and pypdf available.
