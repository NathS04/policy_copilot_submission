# Error Taxonomy

This taxonomy classifies evaluation errors into diagnostic categories that map engineering choices to failure modes. It supports per-baseline and per-configuration error attribution, enabling targeted improvement and ablation analysis.

## Categories

1. **Missed Retrieval** — Relevant document/paragraph exists in corpus but was not in top-k retrieved set. Detected when: answerable query has gold paragraph IDs but none appear in `retrieved_ids_topk`.

2. **Chunk Boundary** — Relevant content partially retrieved but key information split across chunk boundaries. Detected when: some but not all gold paragraph IDs appear in retrieved set, and answer quality is degraded.

3. **Wrong Claim-Evidence Link** — System cites a passage that does not support the generated claim. Detected when: `citations` reference passages not in the gold evidence set, or citation precision is below threshold.

4. **Unsupported Generation** — Model generates claims not grounded in retrieved evidence (hallucination). Detected when: `unsupported_claims` > 0, or system answers an unanswerable query.

5. **Contradiction Ignored** — Conflicting evidence exists (contradiction-category query) but system does not surface contradictions. Detected when: `category` = contradiction but `contradictions_found` = 0 or empty.

6. **Abstention Error** — System abstains when it should answer (false abstention) or answers when it should abstain (missed abstention). Detected when: answerable query has `is_abstained` = True, or unanswerable query has `is_abstained` = False.

7. **Format / Schema Error** — Output did not match expected JSON schema or pipeline raised an exception. Detected when: `error` column is non-empty.

8. **Backend Fallback Effect** — Dense retrieval was requested but BM25 was used due to missing ML dependencies. Detected when: run config shows `backend_requested != backend_used`. This is a system-level category affecting entire runs, not individual queries.

## Usage

The script `scripts/classify_errors.py` applies these rules to `predictions.csv` from each shipped run and produces `results/tables/failure_taxonomy.csv` with per-baseline category counts. Categories are not mutually exclusive: a single query may exhibit multiple failure modes.
