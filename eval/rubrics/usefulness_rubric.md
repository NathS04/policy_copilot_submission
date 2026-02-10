# Usefulness Rubric

Score each system output on these dimensions (1–5 scale):

## U1 – Answer Clarity (1–5)
- **1** = Incomprehensible, irrelevant, or completely wrong
- **2** = Partially addresses the question but confusing or mostly irrelevant
- **3** = Addresses the question but vague or incomplete
- **4** = Clear and mostly complete answer
- **5** = Clear, complete, and well-structured answer that fully addresses the question

## U2 – Actionability (1–5)
- **1** = No actionable information; user cannot act on the answer
- **2** = Vaguely actionable; user might infer some guidance
- **3** = Somewhat actionable; provides general direction
- **4** = Mostly actionable; provides specific guidance with minor gaps
- **5** = Highly actionable; provides precise, specific guidance the user can immediately apply

## Scoring Notes
- An "INSUFFICIENT_EVIDENCE" answer on an unanswerable question: U1=5 (correct), U2=3 (acknowledges limitation)
- An "INSUFFICIENT_EVIDENCE" answer on an answerable question: U1=1 (failed to answer), U2=1
- Abstention is preferable to hallucination for policy questions
