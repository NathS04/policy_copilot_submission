# Independent Reviewer Evaluation Rubric

This document defines the rubric used in the Independent Reviewer
Evaluation reported in Section 4.10 of the dissertation.

## Sample

A fixed sample of 20 query-output pairs from the B3-Generative test
run, balanced across query types so that reviewers see the system's
full behaviour and not only its successes:

| Query type            | Count | Notes                                                                  |
| --------------------- | ----: | ---------------------------------------------------------------------- |
| Answerable, answered  |     8 | Cases the system attempted to answer with cited evidence               |
| Correct abstention    |     4 | Unanswerable / out-of-scope cases the system refused                   |
| Over-abstention       |     4 | Answerable cases the system incorrectly refused                        |
| Contradiction         |     4 | Multi-source-tension cases where the system surfaced conflicts         |
| **Total**             |    20 |                                                                        |

## What reviewers were shown

For each case, reviewers saw:

- the user query
- the system answer (or `INSUFFICIENT_EVIDENCE` with reason)
- the cited evidence paragraphs (paragraph IDs and quoted text)
- the system status badge: *Supported* / *Abstained* / *Contradiction*

Reviewers were *not* shown the baseline label. They knew this was a
research evaluation but not which of B1/B2/B3 produced the output.

## Scoring axes (1-5 Likert)

Each output was scored independently on five axes:

| Axis                | Question to answer                                                               |
| ------------------- | -------------------------------------------------------------------------------- |
| Correctness         | Does the answer (or refusal) match what the cited evidence says?                 |
| Groundedness        | Is every claim in the answer visibly supported by the cited paragraphs?          |
| Citation usefulness | Do the citations help a reader verify the answer themselves?                     |
| Usefulness          | Would the output help a real user answer the underlying policy question?         |
| Trust calibration   | Does the system express appropriate uncertainty / refusal when evidence is weak? |

Each axis was scored from **1 = poor** to **5 = excellent**. For
abstention cases the rubric was simplified:

- Correctness = 5 (appropriate refusal) or 1 (incorrect refusal)
- Groundedness = 5 by definition (no claims made)
- Citation usefulness = scored on whether the *evidence rail* still
  helped the reviewer understand why the system refused
- Usefulness = 3 (correct refusal is useful but not a substantive
  answer) or 1 (over-abstention)
- Trust calibration = subjective judgement of refusal appropriateness

## Free-text comments

Reviewers were also invited to leave a one-line comment per case
describing the strongest or weakest aspect of the output. Comments
were thematically coded after collection (see `thematic_codes.csv`)
and not quoted verbatim in the report.

## Limitations of the design

This is a small **author-facilitated** independent reviewer evaluation,
not a full user study. Specifically:

- Reviewers were technically literate but not professional compliance
  specialists.
- The author was present to answer clarifying questions and so the
  evaluation is not fully blinded.
- Sample size (n = 20 per reviewer, 3-6 reviewers) is small enough
  that point estimates are indicative rather than statistically
  robust.

These caveats are made explicit in Section 4.10 of the dissertation
and in Limitation L5 of the Discussion.
