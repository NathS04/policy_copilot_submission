# Vertical Slice Case Study

This file gives a short walkthrough of three existing Policy Copilot examples.
It is not a new evaluation result. It is included to make the pipeline easier
to inspect.

All three cases are taken verbatim from the B3-Generative final run's
`outputs.jsonl`. The full audit trail for each is in the matching file under
`docs/evidence/verification/`.

## Case A: Answerable query

**Source:** [`audit_export_answerable.md`](audit_export_answerable.md)

**Query:** `q_018` — *What is the minimum password length?*

**Expected behaviour:** The system should answer only if the retrieved evidence
supports the answer.

**Pipeline trace:**

1. Retrieved evidence (top-5): `it_security_addendum_2025::p0003::i0000::d2a928aa94b0`, `dpia_guide::p0004::i0000::f474a88a8052`, `internal_policy_handbook_v2::p0005::i0000::efdcaf0bd522`, `internal_policy_handbook_v2::p0011::i0000::8fcca5a66916`, `internal_policy_handbook_v2::p0005::i0001::33c21bb359ec`.
2. Max rerank score 1.0, mean top-3 rerank 0.8773 — above the abstention threshold of 0.3, so the system goes on to generate.
3. Final cited evidence: `it_security_addendum_2025::p0003::i0000::d2a928aa94b0` (single citation, paragraph 0003 of the IT Security Addendum).
4. Claim verification: `support_rate = 1.0`. No contradictions surfaced.
5. Final response status: **Answered** — *"The minimum password length is now 12 characters, which has been increased from the previous requirement of 8 characters."*

**Why this matters:** the answer is not just fluent; it is tied back to a
specific paragraph in the cited policy document, and the verifier confirms
that every claim in the answer is supported by that paragraph.

## Case B: Unanswerable query

**Source:** [`audit_export_unanswerable.md`](audit_export_unanswerable.md)

**Query:** `q_004` — *Are employees allowed to use personal devices for work?*

**Expected behaviour:** the system should abstain rather than invent missing
policy information. The golden set labels this query as `unanswerable` in the
test split.

**Pipeline trace:**

1. Retrieved evidence (top-5): `internal_policy_handbook_v2::p0014::i0000::22101d8d9bb7`, `internal_policy_handbook_v2::p0003::i0002::4ff99839f515`, `internal_policy_handbook_v2::p0009::i0000::40d044dc00be`, `internal_policy_handbook_v2::p0014::i0003::c79e6cb648ff`, `internal_policy_handbook_v2::p0015::i0002::e695f02f6cd9`.
2. Max rerank score 1.0, mean top-3 rerank 0.9864. The pre-LLM rerank gate passes; the LLM is invoked.
3. Claim verification: `support_rate = 0.6667` (1 unsupported claim out of 3). The post-LLM `min_support_rate` gate fires.
4. Final response status: **Abstained** — `INSUFFICIENT_EVIDENCE`, with the
   notes field recording `ABSTAINED_LOW_SUPPORT_RATE (rate=0.67)` alongside
   the BM25 fallback note.

**Why this matters:** this is where Policy Copilot differs from a normal
chatbot. A refusal counts as a success when the corpus does not contain
enough evidence, and the audit trail records *why* the refusal happened
(rerank gate vs support-rate gate).

## Case C: Contradiction probe

**Source:** [`audit_export_contradiction.md`](audit_export_contradiction.md)

**Query:** `q_057` — *Are visitors both allowed and not allowed in secure areas?*

**Expected behaviour:** the system should surface the conflict rather than
collapse the policy disagreement into one clean sentence.

**Pipeline trace:**

1. Retrieved evidence (top-5): `internal_policy_handbook_v2::p0010::i0001::a429d2df3997`, `it_security_addendum_2025::p0006::i0000::ebbe0ac102b2`, `it_security_addendum_2025::p0006::i0002::7973e328680d`, `internal_policy_handbook_v2::p0014::i0002::051345293182`, `internal_policy_handbook_v2::p0010::i0002::ce27530db5f5`.
2. Five citations attached to the final response.
3. Contradiction detection: `n_contradictions = 5`, each with the structured rationale `'must' vs 'must not'` across the candidate paragraphs.
4. Claim verification: `support_rate = 1.0`. Notes record `CONTRADICTION_SURFACED`.
5. Final response status: **Answered with contradictions surfaced** — the answer explains that visitors *may* enter some secure areas under escort but are *never* permitted in Restricted Zones, and explicitly flags that the cited paragraphs conflict.

**Why this matters:** this case shows why auditability matters. In policy
documents, the safest answer is sometimes to show the conflict rather than
force one clean answer. The structured contradictions list lets a reviewer
inspect exactly which paragraph pairs disagree.

---

These examples are deliberately small. Their purpose is not to add new
results, but to make the main evaluation easier to inspect.
