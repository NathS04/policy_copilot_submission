# Independent Reviewer Evaluation: Participant Information Sheet

Thank you for agreeing to take part in this short evaluation as part of
my University of Leeds COMP3931 Individual Project (Policy Copilot, an
audit-ready retrieval-augmented question-answering system over policy
documents).

## What you will be asked to do

You will be shown 20 query / answer pairs produced by the system. For
each pair you will see:

- The user's question
- The system's answer (or its refusal `INSUFFICIENT_EVIDENCE`)
- The cited evidence paragraphs the system used
- The system status badge: *Supported*, *Abstained*, or *Contradiction*

You will not be told which baseline (B1 / B2 / B3) produced each answer.

For each pair you will give a 1-to-5 score on five axes (Correctness,
Groundedness, Citation Usefulness, Usefulness, Trust Calibration) and
optionally a one-line comment on the strongest or weakest aspect of the
output.

## What data is collected

- Your numeric scores (1-5) on the five rubric axes for each of the 20
  outputs.
- Optionally, a one-line free-text comment per output.

What is **not** collected:

- Your name, email, phone number, course code, or any other personal
  identifier.
- Audio, video, or screenshots.
- Any sensitive personal information.

## How your data is handled

- You will be assigned an anonymous identifier (`P1`, `P2`, ...) before
  any data is recorded.
- Only the anonymous identifier and your role tag (`BSc CS` or `MSc CS`)
  are retained.
- Free-text comments are coded into themes after collection and not
  quoted verbatim in the report.
- The dataset will be archived in the project repository under
  `eval/human_eval/` and reproduced in Appendix B.10 of the
  dissertation.

## Your rights

- Participation is voluntary.
- You may withdraw your data at any point before the dissertation is
  submitted; in that case your rows will be removed from the CSV and
  from any reported aggregates.
- The author will not include your name, contact details, or any quoted
  text that could identify you.

## Time

The evaluation should take roughly 15-25 minutes.

## Contact

For any questions or to withdraw, contact the author at the email used
to invite you to the evaluation.

---

If you have read this information and consent to your anonymised scores
and any optional comments being used in the dissertation, please
indicate "Yes" on the first page of the Google Form before continuing.
