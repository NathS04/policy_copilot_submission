# Groundedness Rubric

Score each system output on these dimensions:

## G0 – Ungrounded Claim Present (Binary)
- **Yes** = at least one claim in the answer is NOT supported by any cited evidence
- **No** = every claim in the answer has supporting evidence in the cited paragraphs

## G1 – Supported Claim Ratio (0.0–1.0)
Count the total claims (sentences making factual assertions) in the answer.
Count how many are supported by information in the cited paragraphs.
- **G1 = supported_claims / total_claims**
- If answer is INSUFFICIENT_EVIDENCE, G1 = N/A

## G2 – Citation Correctness (0–2 scale)
- **0** = Citations are wrong or missing entirely; cited paragraphs do not support the answer
- **1** = Partially correct; some citations support some claims but gaps exist
- **2** = All citations clearly and correctly support the corresponding claims

## Scoring Notes
- An "INSUFFICIENT_EVIDENCE" answer on an unanswerable question is **correct abstention** (G0=No, G1=N/A, G2=N/A)
- An "INSUFFICIENT_EVIDENCE" answer on an answerable question is **unnecessary abstention** (G0=No, G1=N/A, G2=N/A) — note in comments
- A claim is "supported" if the cited paragraph contains information that entails or directly addresses the claim
