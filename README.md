# Audit-Ready Policy Copilot (Dissertation)

**Evidence-Grounded RAG with Citation Enforcement and Reliability Evaluation**

## Overview
This system answers questions over a corpus of policy/standards documents ONLY when it can cite specific supporting paragraphs ("cited or silent"). It features reliability controls (abstention, contradiction surfacing, citation checks) and an audit/critic mode to flag problematic policy language.

## Quick Setup (macOS)

```bash
# 1. Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY / ANTHROPIC_API_KEY
```

## 🔐 Evaluator Instructions
For detailed verification steps (offline/online reproduction), see:
[INSTRUCTIONS_FOR_EVALUATOR.md](INSTRUCTIONS_FOR_EVALUATOR.md)

## Workflow

1.  **Ingestion**: `python scripts/ingest_corpus.py` - Processes PDFs from `data/corpus/raw` into structured JSONL.
2.  **Indexing**: `python scripts/build_index.py` - Builds FAISS vector index from processed data.
3.  **Querying**: `python scripts/query_cli.py "Your question here"` - Runs the RAG pipeline.
4.  **Evaluation**: `python scripts/run_eval.py` - Runs the golden set evaluation.
5.  **UI**: `streamlit run src/policy_copilot/ui/streamlit_app.py` - Launches the web interface.

## Phase 3: Baseline Evaluation

### Environment Keys
Copy `.env.example` to `.env` and add your API key(s):
```bash
cp .env.example .env
# Then edit .env:
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

You can also override settings via `configs/run_config.json`.

### Running Baselines
```bash
# B2 — Naive RAG (retrieves top-5, sends to LLM)
python scripts/run_eval.py --baseline b2 --run_name b2_naive_test

# B1 — Prompt-only (no retrieval, no evidence)
python scripts/run_eval.py --baseline b1 --run_name b1_prompt_only_test

# Both baselines
python scripts/run_eval.py --baseline both --run_name baseline_compare

# Single question with LLM answer
python scripts/query_cli.py "What is the policy on X?" --llm
```

### Output Structure
Each run writes to `results/runs/<run_name>/`:
- `run_config.json` — effective config used
- `outputs.jsonl` — full per-query JSON output
- `predictions.csv` — tabular results
- `README.md` — auto-generated run summary

### RAG Response JSON Schema
```json
{
  "answer": "string (or INSUFFICIENT_EVIDENCE)",
  "citations": ["paragraph_id", ...],
  "notes": "optional string"
}
```

## Phase 4: Full System (B3) — Reliability Layer

### What B3 Does
1. **Retrieve** more candidates (default 20) from FAISS
2. **Rerank** using cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`), keep top-5
3. **Confidence gate**: if `max_rerank_score < abstain_threshold`, abstain
4. **Generate** answer with strict per-sentence `[CITATION: paragraph_id]` enforcement
5. **Claim verification**: split answer into sentences, verify each claim against cited evidence using keyword overlap heuristic (Jaccard > 0.10)
6. **Support enforcement**: if `support_rate < min_support_rate`, abstain; otherwise remove unsupported claims
7. **Contradiction detection**: flag evidence conflicts (negation pairs, numeric mismatches), surface or abstain

### Running B3
```bash
# Full system
python scripts/run_eval.py --baseline b3 --run_name b3_full_system_test

# Ablations
python scripts/run_eval.py --baseline b3 --run_name b3_ablate_no_rerank --no_rerank
python scripts/run_eval.py --baseline b3 --run_name b3_ablate_no_verify --no_verify
python scripts/run_eval.py --baseline b3 --run_name b3_ablate_no_contradictions --no_contradictions

# Config overrides
python scripts/run_eval.py --baseline b3 --abstain_threshold 0.50 --min_support_rate 0.90

# All baselines
python scripts/run_eval.py --baseline all --run_name full_comparison
```

### B3 Output Fields
Each `outputs.jsonl` record includes:
- `confidence` — `{max_rerank, mean_top3_rerank, abstain_threshold}`
- `evidence` — scored evidence array with `score_retrieve` and `score_rerank`
- `claim_verification` — `{claims: [...], supported_claims, unsupported_claims, support_rate}`
- `contradictions` — detected conflicts with `paragraph_ids`, `rationale`, `confidence`
- `latency_ms` — breakdown: `{retrieval_ms, rerank_ms, llm_gen_ms, verify_ms, contradictions_ms}`

### Notes Flags
| Flag | Meaning |
|------|---------|
| `ABSTAINED_LOW_CONFIDENCE` | Max rerank score below threshold |
| `ABSTAINED_LOW_SUPPORT_RATE` | Claim support rate below minimum |
| `UNSUPPORTED_CLAIMS_REMOVED` | Some claims removed due to low support |
| `CONTRADICTION_SURFACED` | Conflicting evidence detected and noted |
| `ABSTAINED_CONTRADICTION_HIGH` | High-confidence contradiction caused abstention |
| `RERANK_FALLBACK` | Cross-encoder failed; used retrieval scores |
| `RERANK_DISABLED` / `VERIFY_DISABLED` / `CONTRADICTIONS_DISABLED` | Ablation active |

### Locked Evaluation Targets (Placeholders)
- **(T1)** ≥30% reduction in ungrounded-claim rate vs B2 on answerable subset
- **(T2)** Abstention accuracy ≥0.80 on unanswerable subset
- **(T3)** Evidence recall@5 ≥0.80 on answerable queries

## Phase 5: Evaluation Package

### Golden Set v1
63 queries with train/dev/test splits (33 answerable, 20 unanswerable, 10 contradiction probes).

```bash
# Generate template from processed paragraphs
python scripts/make_golden_set_template.py

# Interactively label gold IDs (shows top-k retrieval results)
python scripts/assist_label_gold.py --query_id q_018

# Validate golden set integrity
python scripts/validate_golden_set.py
```

### Human Rubric Workflow
Locked rubric scales: groundedness (G0/G1/G2) and usefulness (U1/U2).

```bash
# Export annotation pack from run outputs
python scripts/export_human_eval_pack.py --run_name b3_full_system_test --split test

# Import completed pack (single rater)
python scripts/import_human_eval_pack.py --run_name b3_full_system_test --pack eval/human_eval/packs/...

# Import with two-rater agreement (Cohen's kappa)
python scripts/import_human_eval_pack.py --run_name b3_full_system_test --pack packA.jsonl --pack_b packB.jsonl
```

### Tier-2 LLM Verification
Optional LLM-based claim support verification and contradiction judging. Results cached to JSONL.

Enabled via config or `run_eval.py` flags:
```bash
python scripts/run_eval.py --baseline b3 --enable_llm_verify --run_name b3_llm_verified
```

### Critic Mode (L1–L6)
Detects problematic policy language: normative/loaded (L1), framing imbalance (L2), unsupported claims (L3), internal contradictions (L4), false dilemma (L5), slippery slope (L6).

```bash
# View dataset instructions
python scripts/make_critic_dataset.py --mode manual

# Run heuristic critic evaluation
python scripts/run_critic_eval.py --run_name critic_heuristic --mode heuristic

# Run LLM critic evaluation
python scripts/run_critic_eval.py --run_name critic_llm --mode llm
```

### Figures + Tables
```bash
# Generate figures and tables from results/runs
python eval/analysis/make_figures.py --out_fig_dir results/figures --out_table_dir results/tables
# Outputs: results/figures/fig_baselines.png, fig_retrieval.png, fig_groundedness.png, fig_tradeoff.png
#          results/tables/run_summary.csv
```

## Baselines
- **B1**: Prompt-only LLM — no retrieval; measures hallucination baseline
- **B2**: Naive RAG — top-k=5 evidence, no reranking or abstention
- **B3**: Full system — reranking + confidence-gated abstention + per-claim citation verification + contradiction surfacing

## Reproducibility
The `scripts/run_eval.py` script regenerates the headline results found in `results/`.

### Reproduction Scripts
- **Offline (No API keys, No GPU)**: `python scripts/reproduce_offline.py`
  - Runs B2/B3 in extractive mode using BM25.
  - Generates figures (strict mode).
- **Online (Full Audit)**: `python scripts/reproduce_online.py`
  - Runs B1/B2/B3 in generative mode (requires API keys).
  - Uses dense embeddings and full LLM verification.
  - Fails fast unless dense index files already exist at `data/corpus/processed/index/`.
    Build once with: `python scripts/build_index.py` (after `pip install -e ".[ml]"`).

All requirements are pinned in `requirements.txt`.
