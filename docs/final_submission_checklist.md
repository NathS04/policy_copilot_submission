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
| Final report (PDF) | `docs/report/Final_Report_Nathaniel_Sebastian_201715051.pdf` | A4, generated from markdown via two-pass build |
| Editable source (markdown) | `docs/report/Final_Report_Nathaniel_Sebastian_201715051.md` | Single-file source; LoF / LoT / TOC are markdown lists post-processed by the build script |
| Intermediate DOCX | `docs/report/build_assets/Final_Report_Nathaniel_Sebastian_201715051.docx` | Pandoc + `apply_leeds_template.py` output, retained for rebuilds |
| Build orchestrator | `scripts/build_report.py` | Two-pass build (pagemap then final render) |
| Template post-processor | `scripts/apply_leeds_template.py` | Heading promotion, table styling, TOC / LoF / LoT typography |
| Leeds template / pandoc reference doc | `docs/report/build_assets/Final_Report_Template.docx` | Single retained template; the older `leeds_template.docx` was removed during the May-2026 audit pass and the build now uses this template throughout |

## PDF verification

| Metric | Value |
| --- | --- |
| Total PDF pages | 67 |
| First body page (Chapter 1) | Arabic page 1 (after Roman-numeral preliminaries) |
| Last body page (end of Chapter 5) | Arabic page 32 |
| Body page range (Chapters 1–5) | Arabic pages 1–32 (preliminaries, references, and appendices excluded from the body count, per Deliverables wording) |
| Summary page count | 1 page (Roman preliminaries) |
| Front-matter pages | Roman-numeral preliminaries before Chapter 1 |
| References + Appendices | After the body chapters (excluded from body count) |
| File size | ~1.85 MB |
| PDF link annotations | Internal navigation + external URI links for the GitHub repository |
| External URIs in PDF | GitHub repository link (Appendix B) |

Page counts above are taken from the rebuilt PDF and were not hardcoded earlier in this checklist; re-running `python scripts/build_report.py` will overwrite the PDF but is not expected to change the body chapter range materially.

## Hyperlink verification

The PDF was inspected with `pypdf` to confirm link annotations exist. Internal navigation covers entries in the Table of Contents, List of Figures, and List of Tables; the external URI covers the GitHub repository link in Appendix B. LibreOffice's PDF export embeds these as `/Link` annotations with `/URI` actions, which all standard PDF viewers treat as clickable. (Earlier Deloitte and Pinecone external URIs were removed during the May-2026 audit pass when those bibliography entries were dropped.)

## Tests / report status

The codebase test suite (49 files; 292 collected under the documented
command: 290 passed, 2 conditionally skipped) passes on the submitted
build, as recorded in §B.7.1.

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
- [x] Body chapters precede references and appendices; the body count excludes preliminaries, references, and appendices per the Deliverables wording in the report.
- [x] Summary fits on one A4 page.
- [x] No placeholder or marker strings remain in the PDF (TODO, FIXME,
  XXX, broken cross-reference text, or the truncated-name placeholder
  that previously appeared on the title page).
- [x] Every figure has a caption directly beneath it; every table has a
  caption directly above it.
- [x] All wide tables (B.1, B.2, B.7.x) wrap snake_case identifiers via
  zero-width-space injection so no identifiers split mid-word.
- [x] Two-pass build is reproducible: `python scripts/build_report.py`
  regenerates `Final_Report_Nathaniel_Sebastian_201715051.pdf` from the
  markdown source on a fresh clone with pandoc, LibreOffice, python-docx,
  and pypdf available.
