# Run: b3_generative_final

- **Baseline**: b3
- **Queries processed**: 63
- **Duration**: 177.7s
- **Provider**: openai
- **Model**: gpt-4o-mini
- **Created**: 2026-02-25T04:02:53.729747+00:00

## B3 Configuration
- retrieve_k_candidates: 50
- rerank_k_final: 5
- abstain_threshold: 0.3
- min_support_rate: 0.8
- contradiction_policy: surface

## Ablations
- backend: dense
- allow_fallback: False
- no_rerank: False
- no_verify: False
- no_contradictions: False

## Locked Targets (placeholders)
- (T1) ≥30% reduction in ungrounded-claim rate vs B2
- (T2) abstention accuracy ≥0.80 on unanswerable subset
- (T3) evidence recall@5 ≥0.80 on answerable queries
