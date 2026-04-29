# Audit Export Example - Contradiction

**Source:** `results/runs/b3_generative_bm25_fallback_final/outputs.jsonl` (single line for `query_id = q_057`)
**Generated:** 2026-05-06T00:28:24.129649+00:00

This file is a human-readable rendering of one record from the
B3-Generative final run's `outputs.jsonl`. It demonstrates the
kind of audit trail an examiner can extract for any answer the
system produced. No values are summarised, rounded, or
fabricated; the full record is shown.

## Query

- **query_id:** `q_057`
- **category:** `contradiction`
- **question:** Are visitors both allowed and not allowed in secure areas?

## System decision

- **status:** Answered
- **answer:** Visitors may be granted temporary escorted access to secure areas under specific conditions, such as pre-approval by the IT Operations Manager and being escorted by an authorised employee at all times [CITATION: it_security_addendum_2025::p0006::i0000::ebbe0ac102b2]. However, visitors are never permitted in Restricted Zones, including server rooms and data centres, under any circumstances [CITATION: internal_policy_handbook_v2::p0010::i0002::ce27530db5f5]. Therefore, while there are conditions under which visitors can access certain secure areas, they are explicitly not allowed in Restricted Zones [CITATION: internal_policy_handbook_v2::p0010::i0002::ce27530db5f5]. Note: some evidence sources may conflict on this point ('must' vs 'must not'; 'must' vs 'must not'; 'must' vs 'must not').
- **citations (5):** `it_security_addendum_2025::p0006::i0000::ebbe0ac102b2`, `internal_policy_handbook_v2::p0010::i0002::ce27530db5f5`, `it_security_addendum_2025::p0006::i0002::7973e328680d`, `internal_policy_handbook_v2::p0010::i0001::a429d2df3997`, `internal_policy_handbook_v2::p0014::i0002::051345293182`

## Confidence and abstention gate

- **abstain_threshold:** 0.3
- **max_rerank score:** 1.0
- **mean top-3 rerank:** 0.8564

## Claim verification

- **support_rate:** 1.0
- **n_claims:** n/a
- **threshold (overlap):** n/a

## Contradiction surfacing

- **n_contradictions:** 5
  1. {"type": "contradiction", "paragraph_ids": ["internal_policy_handbook_v2::p0010::i0001::a429d2df3997", "it_security_addendum_2025::p0006::i0002::7973e328680d"], "rationale": "'must' vs 'must not'", "c
  2. {"type": "contradiction", "paragraph_ids": ["internal_policy_handbook_v2::p0010::i0001::a429d2df3997", "internal_policy_handbook_v2::p0014::i0002::051345293182"], "rationale": "'must' vs 'must not'", 
  3. {"type": "contradiction", "paragraph_ids": ["it_security_addendum_2025::p0006::i0002::7973e328680d", "internal_policy_handbook_v2::p0014::i0002::051345293182"], "rationale": "'must' vs 'must not'", "c
  4. {"type": "contradiction", "paragraph_ids": ["it_security_addendum_2025::p0006::i0002::7973e328680d", "internal_policy_handbook_v2::p0010::i0002::ce27530db5f5"], "rationale": "'must' vs 'must not'", "c
  5. {"type": "contradiction", "paragraph_ids": ["internal_policy_handbook_v2::p0014::i0002::051345293182", "internal_policy_handbook_v2::p0010::i0002::ce27530db5f5"], "rationale": "'must' vs 'must not'", 

## Retrieved evidence (top-5)

1. `internal_policy_handbook_v2::p0010::i0001::a429d2df3997`
   - retrieval score: 1.000; rerank score: 1.000
   - text: "Report tailgating incidents to Facilities immediately. The server room and data centre areas are classified as Restricted Zones. Access is limited to authorised IT Operations staff and requires both badge access and biometric verification...."
2. `it_security_addendum_2025::p0006::i0000::ebbe0ac102b2`
   - retrieval score: 0.875; rerank score: 0.875
   - text: "5. Visitor Access to Secure Areas Visitors may be granted temporary escorted access to secure areas, including server rooms, under the following conditions: the visit is pre-approved by the IT Operations Manager, a documented business justi..."
3. `it_security_addendum_2025::p0006::i0002::7973e328680d`
   - retrieval score: 0.694; rerank score: 0.694
   - text: "All visitor activities in Restricted Zones must be logged in real-time by the escort using the Visitor Activity Log (FA-008). Visitors must not bring electronic devices (phones, laptops, cameras) into Restricted Zones without prior written..."
4. `internal_policy_handbook_v2::p0014::i0002::051345293182`
   - retrieval score: 0.637; rerank score: 0.637
   - text: "Personal apps cannot access data within the secure container. The company reserves the right to remotely wipe the secure container if the device is lost, stolen, or if the employee leaves the company. Personal data outside the container is..."
5. `internal_policy_handbook_v2::p0010::i0002::ce27530db5f5`
   - retrieval score: 0.632; rerank score: 0.632
   - text: "Visitors must never be left unattended in any area. Visitor badges must be returned upon departure. Visitors are never permitted in Restricted Zones (server rooms, data centres, security operations centre) under any circumstances, regardles..."

## Run metadata

- **provider:** openai
- **model:** gpt-4o-mini
- **backend_requested:** dense
- **backend_used:** bm25
- **latency:** retrieval_ms=1.6ms, rerank_ms=0.2ms, llm_gen_ms=3781.0ms, verify_ms=0.6ms, contradictions_ms=1.3ms (total 3784.7ms)
- **notes:** RERANK_FALLBACK, CONTRADICTION_SURFACED

## What this demonstrates

The contradiction-detection module surfaced one or more
tensions across the cited paragraphs. The audit trail
preserves both the structured contradictions list and
the candidate evidence so a reviewer can adjudicate.
