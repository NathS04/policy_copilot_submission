# B5 Evidence-Gated Hybrid — Failure Analysis

This document enumerates every false positive (unanswerable surfaced) and false negative (answerable abstained) from `results/runs/b5_evidence_gated_hybrid_v3_final/outputs.jsonl`. It is produced by `scripts/analyse_b5_failures.py` against `eval/golden_set/golden_set_v2_corrected.csv`. Gold paragraph IDs are looked up at analysis time only; they are not used at inference time by the B5 gate.

- False positives (unanswerable surfaced): **2**
- False negatives (answerable abstained):  **4**

## False positives — unanswerable queries B5 still surfaces

### `q_006` — "Is data encryption required for public non-sensitive information?"

- mode_used: `surfaced`
- answerability_reason: `passed_all_gates`
- top_rerank: `0.9959`, top_overlap: `0.0645`, qualifier_in_top: `False`
- top paragraph: `it_security_addendum_2025::p0009::i0000::183a741f2188`
- top text snippet: "8. Encryption Standards Update Encryption of sensitive data at rest is mandatory for all CONFIDENTIAL and RESTRICTED data, using AES-256 or equivalent approved algorithms. This supersedes the more general encryption requirements in the handbook. Data in transit must be protected using TLS 1.3 or hig…"

### `q_017` — "Can part-time employees work remotely?"

- mode_used: `surfaced`
- answerability_reason: `passed_all_gates`
- top_rerank: `0.9936`, top_overlap: `0.0606`, qualifier_in_top: `False`
- top paragraph: `internal_policy_handbook_v2::p0003::i0000::06a108ae6638`
- top text snippet: "2. Remote Work Policy Employees are permitted to work remotely up to 3 days per week, subject to line manager approval. Remote work arrangements must be documented using the Remote Work Agreement Form (HR-007) and renewed every 6 months. All remote work must be performed from a secure, private locat…"

## False negatives — answerable queries B5 abstains on

### `q_020` — "What is the policy on data backup frequency?"

- mode_used: `abstained`
- answerability_reason: `retrieval_weak_top_rerank_below_floor`
- top_rerank: `0.009`, top_overlap: `0.0667`, qualifier_in_top: `True`
- top paragraph: `business_continuity_plan::p0005::i0002::24d4d4d635a9`
- gold paragraph IDs (from golden set, not used at inference):
    - `business_continuity_plan::p0006::i0001::1b79d125164c`
    - `internal_policy_handbook_v2::p0012::i0002::80abfc6468f1`

### `q_023` — "What happens if an employee breaches the data security policy?"

- mode_used: `abstained`
- answerability_reason: `overlap_0.033_below_floor_0.050`
- top_rerank: `0.9851`, top_overlap: `0.0333`, qualifier_in_top: `True`
- top paragraph: `internal_policy_handbook_v2::p0007::i0003::03fcb10e88c0`
- gold paragraph IDs (from golden set, not used at inference):
    - `internal_policy_handbook_v2::p0003::i0003::4ac9f6f1cedd`
    - `internal_policy_handbook_v2::p0007::i0000::4318c9582a70`

### `q_050` — "What are the consequences of non-compliance with security policies?"

- mode_used: `abstained`
- answerability_reason: `overlap_0.045_below_floor_0.050`
- top_rerank: `0.6626`, top_overlap: `0.0455`, qualifier_in_top: `True`
- top paragraph: `internal_policy_handbook_v2::p0013::i0000::0e461b7f55bc`
- gold paragraph IDs (from golden set, not used at inference):
    - `internal_policy_handbook_v2::p0013::i0000::0e461b7f55bc`
    - `dpia_guide::p0006::i0001::6e74bd76ba04`

### `q_062` — "Does the company offer sabbatical leave?"

- mode_used: `abstained`
- answerability_reason: `overlap_0.027_below_floor_0.050`
- top_rerank: `0.729`, top_overlap: `0.027`, qualifier_in_top: `True`
- top paragraph: `hr_procedures_manual::p0006::i0002::8c5195f8b5ea`
- gold paragraph IDs (from golden set, not used at inference):
    - `hr_procedures_manual::p0006::i0002::8c5195f8b5ea`

