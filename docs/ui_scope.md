# UI Scope — Phase 7 Expansion

## Rationale

The Phase 6 UI was a single `st.text_input` that called `Retriever.retrieve()` and
`Answerer.generate_b3()` directly.  It lacked reranking, verification, abstention,
contradiction handling, critic analysis, and any form of audit trail — all of which
are core deliverables of the project specification.

Phase 7 expands the UI into a multi-mode workstation that makes the system's
reliability controls **visible and inspectable**.  This is not cosmetic polish;
it is the primary mechanism by which a reviewer can verify that the pipeline
operates as described in the dissertation.

## Views and Requirement Mapping

| View               | What it does                                         | Requirements served     |
|--------------------|------------------------------------------------------|-------------------------|
| **Ask**            | Chat interface with inline citations and evidence    | FR1, FR2, NFR1, NFR2    |
| **Audit Trace**    | Claim-by-claim verification dossier with export      | FR3, FR4, FR5, NFR3     |
| **Critic Lens**    | L1-L6 policy language analysis                       | FR6, NFR4               |
| **Experiment Explorer** | Browse and compare evaluation runs              | NFR3 (reproducibility)  |
| **Reviewer Mode**  | Human rubric scoring with structured export       | NFR4, evaluation        |

### FR/NFR reference

- **FR1**: Evidence-grounded answers with paragraph-level citations
- **FR2**: Abstention on insufficient evidence
- **FR3**: Claim-evidence mapping and verification
- **FR4**: Contradiction detection and surfacing
- **FR5**: Audit report export (JSON, HTML)
- **FR6**: Critic mode for policy language analysis
- **NFR1**: Usability — modern chat interface
- **NFR2**: Transparency — visible confidence scores and evidence
- **NFR3**: Reproducibility — config snapshots, run browsing
- **NFR4**: Auditability — structured export of every pipeline step

## Architecture Principle

**UI = presentation and state only.**

All business logic lives in `policy_copilot.service`:
- `ChatOrchestrator` handles the full B3 pipeline
- `AuditReportService` handles structured export
- `RunInspector` handles evaluation run browsing
- `ReviewerService` handles human rubric capture and export

The Streamlit layer calls these services and renders the results.
No retrieval, generation, verification, or critic logic is duplicated in UI code.

## What Remains Future Work

- Real-time streaming from LLM (requires async pipeline refactoring)
- PDF export of audit reports
- Multi-document upload with progress tracking
- Multi-rater reviewer sessions with inter-annotator agreement
