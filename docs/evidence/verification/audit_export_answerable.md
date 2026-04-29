# Audit Export Example - Answerable

**Source:** `results/runs/b3_generative_bm25_fallback_final/outputs.jsonl` (single line for `query_id = q_018`)
**Generated:** 2026-05-06T00:28:24.128927+00:00

This file is a human-readable rendering of one record from the
B3-Generative final run's `outputs.jsonl`. It demonstrates the
kind of audit trail an examiner can extract for any answer the
system produced. No values are summarised, rounded, or
fabricated; the full record is shown.

## Query

- **query_id:** `q_018`
- **category:** `answerable`
- **question:** What is the minimum password length?

## System decision

- **status:** Answered
- **answer:** The minimum password length is now 12 characters, which has been increased from the previous requirement of 8 characters. [CITATION: it_security_addendum_2025::p0003::i0000::d2a928aa94b0]
- **citations (1):** `it_security_addendum_2025::p0003::i0000::d2a928aa94b0`

## Confidence and abstention gate

- **abstain_threshold:** 0.3
- **max_rerank score:** 1.0
- **mean top-3 rerank:** 0.8773

## Claim verification

- **support_rate:** 1.0
- **n_claims:** n/a
- **threshold (overlap):** n/a

## Contradiction surfacing

- (no contradictions surfaced)

## Retrieved evidence (top-5)

1. `it_security_addendum_2025::p0003::i0000::d2a928aa94b0`
   - retrieval score: 1.000; rerank score: 1.000
   - text: "2. Enhanced Password Requirements Following a recent security audit, the following enhanced password requirements supersede Section 4 of the Internal Policy Handbook. All passwords must now be a minimum of 12 characters in length (increased..."
2. `dpia_guide::p0004::i0000::f474a88a8052`
   - retrieval score: 0.866; rerank score: 0.866
   - text: "3. DPIA Process Step 1 -- Describe the Processing: Document what personal data is collected, from whom, for what purpose, how it is stored, who has access, and how long it is retained. Include data flow diagrams where helpful. Step 2 -- Ass..."
3. `internal_policy_handbook_v2::p0005::i0000::efdcaf0bd522`
   - retrieval score: 0.766; rerank score: 0.766
   - text: "4. Password and Authentication Policy All employees must use strong passwords for all company systems. Passwords must meet the following minimum requirements: at least 8 characters in length, containing at least one uppercase letter, one lo..."
4. `internal_policy_handbook_v2::p0011::i0000::8fcca5a66916`
   - retrieval score: 0.742; rerank score: 0.742
   - text: "10. Record Retention and Disposal Company records must be retained in accordance with the Record Retention Schedule published by the Legal department. The retention schedule specifies minimum and maximum retention periods by document catego..."
5. `internal_policy_handbook_v2::p0005::i0001::33c21bb359ec`
   - retrieval score: 0.739; rerank score: 0.739
   - text: "The system will enforce this automatically by prompting users 14 days before expiration. Employees who fail to change their password by the deadline will be locked out until IT Support resets their credentials. Password reuse is prohibited..."

## Run metadata

- **provider:** openai
- **model:** gpt-4o-mini
- **backend_requested:** dense
- **backend_used:** bm25
- **latency:** retrieval_ms=1.2ms, rerank_ms=0.2ms, llm_gen_ms=3052.1ms, verify_ms=0.3ms, contradictions_ms=1.0ms (total 3054.7999999999997ms)
- **notes:** RERANK_FALLBACK

## What this demonstrates

Every claim in the answer maps to a real paragraph in the
corpus index, the support_rate from claim verification is
1.0, and no contradictions were surfaced. This is the
audit trail an organisation would archive against a
reviewed policy decision.
