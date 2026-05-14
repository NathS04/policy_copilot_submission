# Run: ablation_full_hybrid_v2

- **Baseline**: b3
- **Queries processed**: 63
- **Duration**: 17.8s
- **Provider**: openai
- **Model**: gpt-4o-mini
- **Created**: 2026-05-14T08:56:55.211723+00:00

## B3 Configuration
- retrieve_k_candidates: 50
- rerank_k_final: 5
- abstain_threshold: 0.3
- min_support_rate: 0.8
- contradiction_policy: surface

## Ablations
- backend: hybrid
- allow_fallback: True
- no_rerank: False
- no_verify: False
- no_contradictions: False

## Locked Targets (placeholders)
- (T1) ≥30% reduction in ungrounded-claim rate vs B2
- (T2) abstention accuracy ≥0.80 on unanswerable subset
- (T3) evidence recall@5 ≥0.80 on answerable queries
