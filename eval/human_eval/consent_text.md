# Independent Reviewer Evaluation: Participant Information and Consent

This document records the participant information and consent process
used for the Independent Reviewer Evaluation reported in Section 4.10
of the dissertation.

## Participant information

Each reviewer was informed of the following before scoring any
outputs:

- The evaluation is part of an undergraduate dissertation project at
  the University of Leeds (COMP3931 Individual Project) on
  retrieval-augmented question answering over policy documents.
- The system being evaluated is a research prototype, not a deployed
  product, and the policy corpus used is *synthetic* (designed for
  this project) rather than any real organisation's documents.
- Reviewers were asked to score 20 query-output pairs on five
  rubric axes (Correctness, Groundedness, Citation Usefulness,
  Usefulness, Trust Calibration), each on a 1-5 Likert scale.
- Each reviewer was free to add a one-line comment per case if they
  wished.

## Data collected

Only the following was collected from each reviewer:

- Numeric scores (1-5) on the five rubric axes
- Optional one-line comments (at most one per case)

The following was **not** collected:

- Names, emails, phone numbers, or any other personal identifiers
- Course codes, year of study, or other potentially identifying
  details
- Audio or video recordings
- Screenshots of devices or messaging apps
- Any sensitive personal information

## Anonymisation

Each reviewer was assigned an anonymous identifier `P1`, `P2`, ...
prior to any score being recorded. Only those identifiers appear in
`independent_review_results.csv` and in the dissertation report. The
mapping from real names to participant IDs has not been retained.

## Consent and withdrawal

Each reviewer confirmed (in writing or by reply) that:

- They were happy for their anonymised scores and any optional
  comments to be used in the dissertation evaluation.
- They understood they could withdraw their data at any point before
  the dissertation was submitted, in which case all of their rows
  would be removed from the CSV and from any reported aggregates.
- They understood that the report would not include their name,
  contact details, or any quoted text that could identify them.

No participant chose to withdraw.

## Use of comments in the report

Free-text comments were thematically coded after collection (see
`thematic_codes.csv`). The dissertation reports only the *frequency*
of each theme across reviewers and a short paraphrase of the theme,
not verbatim quotes. This avoids inadvertent re-identification through
recognisable phrasing.

## Alignment with policy

This evaluation was designed to comply with:

- The University of Leeds Generative AI policy (COMP3931 Amber
  category). The system being evaluated uses LLMs and the evaluation
  data was processed through it; both are documented in Appendix B.5.
- The University of Leeds proof-reading policy. The reviewer
  evaluation is **not** proof-reading: reviewers scored a fixed sample
  of *system outputs*, not the dissertation prose, and were not asked
  to comment on, edit, or rewrite the report.
- The COMP3931 ethics guidance on user testing: participants received
  information about the project and their data; no sensitive personal
  information was collected; participants could withdraw freely.

## Limitations

The evaluation is **author-facilitated** rather than fully blinded:
the author distributed the scoring sheet and was present to answer
clarifying questions about how the rubric should be applied. This is
explicitly acknowledged as a limitation in Section 4.10 and in
Limitation L5 of the Discussion.
