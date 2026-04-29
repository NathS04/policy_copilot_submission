# Audit Export Example - Unanswerable / Abstained

**Source:** `results/runs/b3_generative_bm25_fallback_final/outputs.jsonl` (single line for `query_id = q_004`)
**Generated:** 2026-05-06T00:28:24.129479+00:00

This file is a human-readable rendering of one record from the
B3-Generative final run's `outputs.jsonl`. It demonstrates the
kind of audit trail an examiner can extract for any answer the
system produced. No values are summarised, rounded, or
fabricated; the full record is shown.

## Query

- **query_id:** `q_004`
- **category:** `unanswerable`
- **question:** Are employees allowed to use personal devices for work?

## System decision

- **status:** Abstained
- **answer:** INSUFFICIENT_EVIDENCE
- **citations (0):** (none)

## Confidence and abstention gate

- **abstain_threshold:** 0.3
- **max_rerank score:** 1.0
- **mean top-3 rerank:** 0.9864

## Claim verification

- **support_rate:** 0.6667
- **n_claims:** n/a
- **unsupported_claims:** 1
- **threshold (overlap):** n/a

## Contradiction surfacing

- (no contradictions surfaced)

## Retrieved evidence (top-5)

1. `internal_policy_handbook_v2::p0014::i0000::22101d8d9bb7`
   - retrieval score: 1.000; rerank score: 1.000
   - text: "13. Bring Your Own Device (BYOD) Policy Employees may use personal devices (smartphones, tablets, laptops) for work purposes subject to the conditions in this section. BYOD enrolment requires completion of the BYOD Agreement Form (IT-012) a..."
2. `internal_policy_handbook_v2::p0003::i0002::4ff99839f515`
   - retrieval score: 0.983; rerank score: 0.983
   - text: "Flexible scheduling outside core hours requires written approval from the department head. Remote workers must use company-provided equipment and connect through the corporate VPN at all times. Use of personal devices for work purposes is g..."
3. `internal_policy_handbook_v2::p0009::i0000::40d044dc00be`
   - retrieval score: 0.977; rerank score: 0.977
   - text: "8. Acceptable Use of IT Resources Company IT resources, including email, internet, software, and hardware, are provided for business purposes. Limited personal use is permitted provided it does not interfere with work duties, consume excess..."
4. `internal_policy_handbook_v2::p0014::i0003::c79e6cb648ff`
   - retrieval score: 0.811; rerank score: 0.811
   - text: "CONFIDENTIAL data may only be accessed (not downloaded) through the secure container. Employees are responsible for the physical security of their personal devices. Lost or stolen devices must be reported to IT Security within 2 hours."
5. `internal_policy_handbook_v2::p0015::i0002::e695f02f6cd9`
   - retrieval score: 0.724; rerank score: 0.724
   - text: "Mobile hotspot is the preferred connection method. Upon return from high-risk travel, loaner devices must be returned to IT Security for forensic inspection before being reissued. Any personal devices used during travel should be submitted..."

## Run metadata

- **provider:** openai
- **model:** gpt-4o-mini
- **backend_requested:** dense
- **backend_used:** bm25
- **latency:** retrieval_ms=1.4ms, rerank_ms=0.2ms, llm_gen_ms=3553.5ms, verify_ms=0.6ms (total 3555.7ms)
- **notes:** RERANK_FALLBACK, ABSTAINED_LOW_SUPPORT_RATE (rate=0.67)

## What this demonstrates

The system refused with `INSUFFICIENT_EVIDENCE` rather
than answer. Either the rerank confidence fell below
`abstain_threshold` or the post-LLM `min_support_rate`
gate fired (see notes); the audit trail records both the
reason and the candidate evidence the system saw.
