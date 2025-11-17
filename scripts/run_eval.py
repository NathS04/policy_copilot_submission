"""
Evaluation runner for baselines B1 (prompt-only), B2 (naive RAG), and B3 (full system).
Reads the golden set, runs the selected baseline, and writes results.
B3 includes: reranking, confidence gating, per-claim verification, contradiction surfacing.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ensure project root is on sys.path for eval.metrics imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from tqdm import tqdm

from policy_copilot.config import settings
from policy_copilot.generate.answerer import Answerer
from policy_copilot.retrieve.retriever import Retriever
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def _ensure_run_dir(run_dir: Path):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "cache").mkdir(exist_ok=True)


def _load_existing_outputs(outputs_path: Path) -> set[str]:
    """Return set of query_ids already processed (for caching / resume)."""
    done = set()
    if outputs_path.exists():
        with open(outputs_path, "r") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    done.add(obj.get("query_id", ""))
                except json.JSONDecodeError:
                    pass
    return done


def _json_safe(value):
    """Recursively convert values to JSON-serialisable forms."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _write_run_readme(run_dir: Path, baseline: str, total: int,
                      duration_s: float, cfg: dict, ablations: dict | None = None):
    with open(run_dir / "README.md", "w") as f:
        f.write(f"# Run: {run_dir.name}\n\n")
        f.write(f"- **Baseline**: {baseline}\n")
        f.write(f"- **Queries processed**: {total}\n")
        f.write(f"- **Duration**: {duration_s:.1f}s\n")
        f.write(f"- **Provider**: {cfg.get('provider')}\n")
        f.write(f"- **Model**: {cfg.get('model')}\n")
        f.write(f"- **Created**: {datetime.now(timezone.utc).isoformat()}\n")
        if baseline == "b3":
            f.write("\n## B3 Configuration\n")
            f.write(f"- retrieve_k_candidates: {cfg.get('retrieve_k_candidates')}\n")
            f.write(f"- rerank_k_final: {cfg.get('rerank_k_final')}\n")
            f.write(f"- abstain_threshold: {cfg.get('abstain_threshold')}\n")
            f.write(f"- min_support_rate: {cfg.get('min_support_rate')}\n")
            f.write(f"- contradiction_policy: {cfg.get('contradiction_policy')}\n")
            if ablations:
                f.write("\n## Ablations\n")
                for k, v in ablations.items():
                    f.write(f"- {k}: {v}\n")
        f.write("\n## Locked Targets (placeholders)\n")
        f.write("- (T1) ≥30% reduction in ungrounded-claim rate vs B2\n")
        f.write("- (T2) abstention accuracy ≥0.80 on unanswerable subset\n")
        f.write("- (T3) evidence recall@5 ≥0.80 on answerable queries\n")


# ------------------------------------------------------------------ #
#  B3 pipeline step functions                                          #
# ------------------------------------------------------------------ #

def _run_b3_query(question: str, category: str, retriever: Retriever,
                  answerer: Answerer, ablations: dict, cfg: dict,
                  run_dir: Path, query_id: str) -> dict:
    """Execute the full B3 pipeline for a single query."""
    from policy_copilot.rerank.reranker import Reranker
    from policy_copilot.verify.abstain import compute_confidence, should_abstain
    from policy_copilot.verify.claim_split import split_claims, extract_all_citations
    from policy_copilot.verify.citation_check import verify_claims, enforce_support_policy
    from policy_copilot.verify.contradictions import detect_contradictions, apply_contradiction_policy

    rerank_enabled = not ablations.get("no_rerank", False)
    verify_enabled = not ablations.get("no_verify", False)
    contradictions_enabled = not ablations.get("no_contradictions", False)

    timings = {}
    notes_list = []

    # --- Step 1: Retrieve candidates ---
    retrieve_k = cfg.get("retrieve_k_candidates", 20)
    t0 = time.time()
    candidates = retriever.retrieve(question, k=retrieve_k)
    timings["retrieval_ms"] = round((time.time() - t0) * 1000, 1)
    backend_requested = cfg.get("backend_requested", cfg.get("backend", "unknown"))
    backend_used = getattr(retriever, "backend_used", cfg.get("backend_used", backend_requested))

    # --- Step 2: Rerank (if enabled) ---
    rerank_k = cfg.get("rerank_k_final", 5)
    t0 = time.time()
    if rerank_enabled:
        reranker = Reranker(model_name=cfg.get("rerank_model", "cross-encoder/ms-marco-MiniLM-L-6-v2"))
        top_evidence = reranker.rerank(question, candidates, top_k=rerank_k)
        if reranker.fallback:
            notes_list.append("RERANK_FALLBACK")
    else:
        # no rerank: just use top retrieval results
        for c in candidates:
            c["score_retrieve"] = c.get("score", 0.0)
            c["score_rerank"] = c.get("score", 0.0)
        top_evidence = candidates[:rerank_k]
        notes_list.append("RERANK_DISABLED")
    timings["rerank_ms"] = round((time.time() - t0) * 1000, 1)

    # --- Step 3: Compute confidence and check abstention ---
    confidence = compute_confidence(top_evidence)
    confidence["abstain_threshold"] = cfg.get("abstain_threshold", 0.30)

    if should_abstain(confidence, cfg.get("abstain_threshold", 0.30)):
        # abstain
        return {
            "query_id": query_id,
            "baseline": "b3",
            "question": question,
            "category": category,
            "is_answerable": (category == "answerable"),
            "answer": "INSUFFICIENT_EVIDENCE",
            "is_abstained": True,
            "citations": [],
            "confidence": confidence,
            "evidence": [_evidence_entry(e) for e in top_evidence],
            "claim_verification": None,
            "contradictions": [],
            "notes": ["ABSTAINED_LOW_CONFIDENCE"] + notes_list,
            "provider": cfg.get("provider", ""),
            "model": cfg.get("model", ""),
            "latency_ms": timings,
            "backend_requested": backend_requested,
            "backend_used": backend_used,
        }

            # --- Step 4: Generate answer ---
    t0 = time.time()
    try:
        resp, meta = answerer.generate_b3(question, top_evidence,
                                          allow_fallback=ablations.get("allow_fallback", False))
    except Exception as e:
        logger.error(f"B3 generation failed for {query_id}: {e}")
        return {
            "query_id": query_id, "baseline": "b3", "question": question,
            "category": category, "is_answerable": (category == "answerable"), "answer": "ERROR", "is_abstained": False,
            "citations": [], "confidence": confidence,
            "evidence": [_evidence_entry(e) for e in top_evidence],
            "claim_verification": None, "contradictions": [],
            "notes": [f"ERROR: {e}"] + notes_list,
            "provider": cfg.get("provider", ""),
            "model": cfg.get("model", ""),
            "latency_ms": timings,
            "backend_requested": backend_requested,
            "backend_used": backend_used,
        }
    timings["llm_gen_ms"] = round(meta.get("latency_ms", 0), 1)

    answer = resp.answer
    citations = resp.citations
    if resp.notes:
        notes_list.append(resp.notes)

    # --- Step 5 & 6: Claim verification (if enabled) ---
    claim_verification = None
    if verify_enabled and answer != "INSUFFICIENT_EVIDENCE":
        t0 = time.time()
        # parse claims from answer
        claims = split_claims(answer)
        # extract per-claim citations (from the inline tags)
        # also extract global citations from the raw answer
        inline_cites = extract_all_citations(answer)
        if inline_cites:
            # merge inline citations into the global list
            for c in inline_cites:
                if c not in citations:
                    citations.append(c)

        # build evidence lookup
        evidence_lookup = {e.get("paragraph_id", ""): e.get("text", "")
                          for e in top_evidence}

        # validate citations are in evidence set
        valid_ids = set(evidence_lookup.keys())
        citations = [c for c in citations if c in valid_ids]

        # verify claims
        claim_verification = verify_claims(claims, evidence_lookup,
                                           overlap_threshold=0.10)

        # enforce support policy
        min_sr = cfg.get("min_support_rate", 0.80)
        answer, citations, enforce_notes = enforce_support_policy(
            answer, citations, claim_verification, min_sr
        )
        notes_list.extend(enforce_notes)
        timings["verify_ms"] = round((time.time() - t0) * 1000, 1)
    else:
        if not verify_enabled:
            notes_list.append("VERIFY_DISABLED")

    # --- Step 7: Contradiction detection (if enabled) ---
    contradictions = []
    if contradictions_enabled and answer != "INSUFFICIENT_EVIDENCE":
        t0 = time.time()
        contradictions = detect_contradictions(
            top_evidence,
            enable_llm=cfg.get("enable_llm_contradictions", False)
        )
        if contradictions:
            answer, citations, contra_notes = apply_contradiction_policy(
                answer, citations, contradictions,
                policy=cfg.get("contradiction_policy", "surface")
            )
            notes_list.extend(contra_notes)
        timings["contradictions_ms"] = round((time.time() - t0) * 1000, 1)
    else:
        if not contradictions_enabled:
            notes_list.append("CONTRADICTIONS_DISABLED")

    is_abstained = answer == "INSUFFICIENT_EVIDENCE"

    return {
        "query_id": query_id,
        "baseline": "b3",
        "question": question,
        "category": category,
        "is_answerable": (category == "answerable"),
        "answer": answer,
        "is_abstained": is_abstained,
        "citations": citations,
        "confidence": confidence,
        "evidence": [_evidence_entry(e) for e in top_evidence],
        "claim_verification": claim_verification,
        "contradictions": contradictions,
        "notes": notes_list,
        "provider": meta.get("provider", cfg.get("provider", "")),
        "model": meta.get("model", cfg.get("model", "")),
        "latency_ms": timings,
        "backend_requested": backend_requested,
        "backend_used": backend_used,
    }


def _evidence_entry(e: dict) -> dict:
    """Build a clean evidence entry for the output."""
    return {
        "paragraph_id": e.get("paragraph_id", ""),
        "doc_id": e.get("doc_id", ""),
        "page": e.get("page", 0),
        "score_retrieve": round(e.get("score_retrieve", e.get("score", 0.0)), 4),
        "score_rerank": round(e.get("score_rerank", 0.0), 4),
        "text": e.get("text", "")[:500],  # truncate for output size
    }


# ------------------------------------------------------------------ #
#  Run single baseline (B1, B2, or B3)                                 #
# ------------------------------------------------------------------ #

def run_baseline(baseline: str, golden_path: str, run_name: str,
                 force: bool = False, ablations: dict | None = None,
                 split: str = "all", cli_args: dict | None = None):
    """Run a single baseline ('b1', 'b2', or 'b3') over the golden set."""
    ablations = ablations or {}
    if baseline == "b1" and ablations.get("allow_fallback"):
        raise ValueError("B1 (Prompt-only) requires GENERATIVE mode. Cannot run in extractive mode.")
    run_dir = settings.get_output_dir(run_name)
    _ensure_run_dir(run_dir)

    # save effective config (required for make_figures and verify_artifacts)
    cfg = settings.to_dict()
    cfg["baseline"] = baseline
    cfg["ablations"] = ablations
    cfg["split"] = split
    cfg["mode"] = settings.MODE if hasattr(settings, "MODE") else ("extractive" if not settings.ENABLE_LLM else "generative")
    cfg["backend_requested"] = ablations.get("backend", os.environ.get("POLICY_COPILOT_BACKEND", "dense"))
    cfg["backend"] = cfg["backend_requested"]  # backward-compatible alias
    cfg["backend_used"] = cfg["backend_requested"]
    cfg["enable_llm"] = getattr(settings, "ENABLE_LLM", True)
    cfg["allow_fallback"] = ablations.get("allow_fallback", False)
    cfg["cli_args"] = _json_safe(cli_args or {})
    cfg["thresholds"] = {
        "abstain_threshold": getattr(settings, "ABSTAIN_THRESHOLD", None),
        "min_support_rate": getattr(settings, "MIN_SUPPORT_RATE", None),
    }

    # load golden set
    df = pd.read_csv(golden_path)
    if split != "all" and "split" in df.columns:
        df = df[df["split"] == split].reset_index(drop=True)
    logger.info(f"Loaded {len(df)} queries from {golden_path} (split={split})")

    # caching: skip already-done queries unless forced
    outputs_path = run_dir / "outputs.jsonl"
    done_ids = set() if force else _load_existing_outputs(outputs_path)
    if done_ids:
        logger.info(f"Resuming — {len(done_ids)} queries already cached")

    # prepare components
    answerer = Answerer()
    retriever = None
    if baseline in ("b2", "b3"):
        retriever = Retriever(backend=cfg["backend_requested"])
        cfg["backend_used"] = retriever.backend_used
    with open(run_dir / "run_config.json", "w") as f:
        json.dump(cfg, f, indent=2)
    if baseline in ("b2", "b3"):
        if not retriever.loaded:
            logger.error("FAISS index not loaded. Run build_index.py first.")
            return

    # open output files in append mode
    pred_rows = []
    start_time = time.time()

    with open(outputs_path, "a") as out_f:
        for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Running {baseline.upper()}"):
            qid = str(row.get("query_id", ""))
            question = str(row.get("question", ""))
            category = str(row.get("category", ""))

            if qid in done_ids:
                continue

            if baseline == "b3":
                # full B3 pipeline
                record = _run_b3_query(
                    question, category, retriever, answerer,
                    ablations, cfg, run_dir, qid
                )
                cfg["backend_used"] = getattr(retriever, "backend_used", cfg["backend_used"])
                record["backend_requested"] = cfg["backend_requested"]
                record["backend_used"] = cfg["backend_used"]
            else:
                # B1 or B2
                evidence = []
                retrieved_ids = []
                backend_used = cfg["backend_used"]

                if baseline == "b2" and retriever is not None:
                    evidence = retriever.retrieve(question, k=settings.TOP_K)
                    backend_used = getattr(retriever, "backend_used", backend_used)
                    cfg["backend_used"] = backend_used
                    retrieved_ids = [e["paragraph_id"] for e in evidence]

                try:
                    allow_fallback = ablations.get("allow_fallback", False)
                    if baseline == "b1":
                        if allow_fallback: 
                             # B1 (prompt-only) makes no sense in extractive mode (no LLM, no evidence).
                             raise ValueError("B1 (Prompt-only) requires GENERATIVE mode. Step skipped.")
                        resp, meta = answerer.generate_prompt_only(question)
                    else:
                        resp, meta = answerer.generate_naive_rag(question, evidence, allow_fallback=allow_fallback)
                except Exception as e:
                    logger.error(f"Error on {qid}: {e}")
                    resp = None
                    meta = {"latency_ms": 0, "error": str(e)}

                record = {
                    "query_id": qid,
                    "category": category,
                    "is_answerable": (category == "answerable"),
                    "question": question,
                    "baseline": baseline,
                    "answer": resp.answer if resp else "ERROR",
                    "is_abstained": (resp.answer == "INSUFFICIENT_EVIDENCE") if resp else False,
                    "citations": resp.citations if resp else [],
                    "notes": [resp.notes] if resp and resp.notes else [str(meta.get("error", ""))],
                    "retrieved_paragraph_ids": retrieved_ids,
                    "provider": meta.get("provider", ""),
                    "model": meta.get("model", ""),
                    "latency_ms": meta.get("latency_ms", 0),
                    "backend_requested": cfg["backend_requested"],
                    "backend_used": backend_used,
                }

            # Add golden set info to record for metrics
            record["gold_paragraph_ids"] = str(row.get("gold_paragraph_ids", ""))
            record["gold_doc_ids"] = str(row.get("gold_doc_ids", ""))

            out_f.write(json.dumps(record) + "\n")
            out_f.flush()
            pred_rows.append(record)

    # write predictions CSV (flat)
    preds_path = run_dir / "predictions.csv"
    flat_rows = []
    for r in pred_rows:
        latency = r.get("latency_ms", 0)
        if isinstance(latency, dict):
            latency_total = sum(latency.values())
        else:
            latency_total = latency

        conf = r.get("confidence", {})
        cv = r.get("claim_verification", {})

        flat_rows.append({
            "query_id": r["query_id"],
            "category": r.get("category", ""),
            "question": r.get("question", ""),
            "answer": r.get("answer", ""),
            "is_abstained": r.get("is_abstained", False),
            "citations": str(r.get("citations", [])),
            "retrieved_ids_topk": str([e.get("paragraph_id", "") for e in r.get("evidence", [])] if "evidence" in r else r.get("retrieved_paragraph_ids", [])),
            "confidence_max": conf.get("max_rerank", "") if conf else "",
            "confidence_mean_top3": conf.get("mean_top3_rerank", "") if conf else "",
            "support_rate": cv.get("support_rate", "") if cv else "",
            "unsupported_claims": cv.get("unsupported_claims", "") if cv else "",
            "contradictions_found": len(r.get("contradictions", [])),
            "provider": r.get("provider", ""),
            "model": r.get("model", ""),
            "latency_total_ms": round(latency_total, 1),
            "error": "",
        })

    if preds_path.exists() and not force:
        existing = pd.read_csv(preds_path)
        combined = pd.concat([existing, pd.DataFrame(flat_rows)], ignore_index=True)
        combined.to_csv(preds_path, index=False)
    else:
        pd.DataFrame(flat_rows).to_csv(preds_path, index=False)

    duration = time.time() - start_time
    with open(run_dir / "run_config.json", "w") as f:
        json.dump(cfg, f, indent=2)
    _write_run_readme(run_dir, baseline, len(pred_rows), duration, cfg, ablations)

    # compute & write summary metrics
    _write_summary_metrics(run_dir, pred_rows, baseline)

    logger.info(f"Done. {len(pred_rows)} queries processed in {duration:.1f}s")
    logger.info(f"Results at: {run_dir}")


# Answers that must NOT count as "answered" for answer_rate or citation metrics
NON_ANSWERS = {"INSUFFICIENT_EVIDENCE", "LLM_DISABLED", "ERROR", None}


def _write_summary_metrics(run_dir: Path, records: list[dict], baseline: str):
    """Compute and write summary.json + metrics.csv for the run.
    answered = answer not in NON_ANSWERS. Citation metrics only over answered records.
    """
    from eval.metrics.abstention_metrics import calculate_abstention_accuracy
    from eval.metrics.citation_metrics import calculate_citation_precision, calculate_citation_recall, calculate_ungrounded_rate
    from eval.metrics.retrieval_metrics import calculate_recall_at_k, calculate_precision_at_k, calculate_mrr

    summary = {"baseline": baseline, "total_queries": len(records)}

    # -- 1. Basic Response Metrics (honest: do not count LLM_DISABLED or ERROR as answered) --
    answerable = [r for r in records if r.get("category") == "answerable"]
    unanswerable = [r for r in records if r.get("category") == "unanswerable"]
    contradiction = [r for r in records if r.get("category") == "contradiction"]

    if answerable:
        answered = [r for r in answerable if (r.get("answer") or "").strip() not in NON_ANSWERS and bool((r.get("answer") or "").strip())]
        summary["answer_rate"] = round(len(answered) / len(answerable), 4)

    if unanswerable:
        summary["abstention_accuracy"] = calculate_abstention_accuracy(
            [r.get("answer", "") for r in unanswerable],
            ["INSUFFICIENT_EVIDENCE"] * len(unanswerable)
        )

    # -- 2. Retrieval Metrics --
    # Compute over ALL queries that have gold_paragraph_ids (answerable + contradiction usually)
    retrieval_recalls = []
    retrieval_precs = []
    retrieval_mrrs = []

    for r in records:
        gold_raw = r.get("gold_paragraph_ids", "")
        if not gold_raw or gold_raw.lower() == "nan":
            continue
        gold_ids = [x.strip() for x in gold_raw.split(",") if x.strip()]
        
        # retrieved ids depends on baseline
        if "evidence" in r:
            retreived = [e.get("paragraph_id", "") for e in r.get("evidence", [])]
        else:
            retreived = r.get("retrieved_paragraph_ids", [])

        retrieval_recalls.append(calculate_recall_at_k(retreived, gold_ids, k=5))
        retrieval_precs.append(calculate_precision_at_k(retreived, gold_ids, k=5))
        retrieval_mrrs.append(calculate_mrr(retreived, gold_ids))

    if retrieval_recalls:
        summary["evidence_recall_at_5"] = round(sum(retrieval_recalls) / len(retrieval_recalls), 4)
        summary["evidence_precision_at_5"] = round(sum(retrieval_precs) / len(retrieval_precs), 4)
        summary["evidence_mrr"] = round(sum(retrieval_mrrs) / len(retrieval_mrrs), 4)


    # -- 3. Citation Metrics (only over answerable queries that were actually answered) --
    citation_precs = []
    citation_recalls = []
    answered_list = [r for r in answerable if (r.get("answer") or "").strip() not in NON_ANSWERS and bool((r.get("answer") or "").strip())]

    for r in answered_list:
        gold_raw = r.get("gold_paragraph_ids", "")
        gold_ids = [x.strip() for x in gold_raw.split(",") if x.strip()] if (gold_raw and gold_raw.lower() != "nan") else []
        
        # citations might be list of strings now
        cites = r.get("citations", [])
        # ensure list of strings
        if isinstance(cites, str):
            # if loaded from CSV it might be string repr
            try:
                cites = json.loads(cites.replace("'", '"')) # risky parse
            except json.JSONDecodeError:
                cites = []
        
        # retrieved IDs for precision check
        if "evidence" in r:
            retreived = [e.get("paragraph_id", "") for e in r.get("evidence", [])]
        else:
            retreived = r.get("retrieved_paragraph_ids", [])

        citation_precs.append(calculate_citation_precision(cites, retreived))
        citation_recalls.append(calculate_citation_recall(cites, gold_ids))

    if citation_precs:
        summary["citation_precision"] = round(sum(citation_precs) / len(citation_precs), 4)
        summary["citation_recall"] = round(sum(citation_recalls) / len(citation_recalls), 4)


    # -- 4. Groundedness (B3 only); do not default to 0.0 if verification not performed --
    if baseline == "b3":
        ur = calculate_ungrounded_rate(records)
        summary["ungrounded_rate"] = ur if ur is not None else "N/A"

        support_rates = []
        for r in answered_list:
            cv = r.get("claim_verification")
            if cv is not None and "support_rate" in cv:
                support_rates.append(cv.get("support_rate"))
        if support_rates:
            summary["support_rate_mean"] = round(sum(support_rates) / len(support_rates), 4)


    # -- 5. Contradiction Metrics --
    # Recall: fraction of contradiction queries where contradictions were explicitly found
    if contradiction:
        detected = 0
        for r in contradiction:
            # Check if we found contradictions (B3) or if the answer mentions contradiction (B1/B2 heuristic?)
            # For B3, we have "contradictions" list
            raw_contras = r.get("contradictions", [])
            if raw_contras:
                detected += 1
        summary["contradiction_recall"] = round(detected / len(contradiction), 4)
    
    # Precision: fraction of queries with detected contradictions that are actually in 'contradiction' category
    # (Checking false positives in answerable/unanswerable)
    total_detected = 0
    true_positive_detected = 0
    for r in records:
        if r.get("contradictions"):
            total_detected += 1
            if r.get("category") == "contradiction":
                true_positive_detected += 1
    
    if total_detected > 0:
        summary["contradiction_precision"] = round(true_positive_detected / total_detected, 4)
    else:
        summary["contradiction_precision"] = "N/A"


    # write summary
    with open(run_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # write metrics CSV
    tables_dir = run_dir / "tables"
    tables_dir.mkdir(exist_ok=True)
    pd.DataFrame([summary]).to_csv(tables_dir / "metrics.csv", index=False)


# ------------------------------------------------------------------ #
#  CLI                                                                 #
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="Run baseline evaluations on the Golden Set.")
    parser.add_argument("--baseline", choices=["b1", "b2", "b3", "both", "all"],
                        default="all", help="Which baseline to run")
    parser.add_argument("--run_name", default=None,
                        help="Name for this run (default: auto timestamp)")
    parser.add_argument("--golden_set", default=settings.GOLDEN_SET_PATH,
                        help="Path to golden set CSV")
    parser.add_argument("--split", choices=["dev", "test", "all"],
                        default="all", help="Filter golden set by split column")
    parser.add_argument("--config", default=None,
                        help="Path to a JSON config file to override settings")
    parser.add_argument("--force", action="store_true",
                        help="Re-run all queries even if cached")

    # B3 ablation flags
    parser.add_argument("--no_rerank", action="store_true",
                        help="[B3] Disable cross-encoder reranking")
    parser.add_argument("--no_verify", action="store_true",
                        help="[B3] Disable per-claim citation verification")
    parser.add_argument("--no_contradictions", action="store_true",
                        help="[B3] Disable contradiction detection")

    # B3 config overrides
    parser.add_argument("--retrieve_k_candidates", type=int, default=50,
                        help="[B3] Number of candidates to retrieve. Default increased to 50 for better recall.")
    parser.add_argument("--rerank_k_final", type=int, default=None,
                        help="[B3] Number of top results to keep after reranking")
    parser.add_argument("--abstain_threshold", type=float, default=None,
                        help="[B3] Confidence threshold for abstention")
    parser.add_argument("--min_support_rate", type=float, default=None,
                        help="[B3] Minimum claim support rate before abstaining")
    parser.add_argument("--enable_llm_verify", type=str, default=None,
                        help="[B3] Enable LLM-based claim verification (true/false)")
    parser.add_argument("--enable_llm_contradictions", type=str, default=None,
                        help="[B3] Enable LLM-based contradiction detection (true/false)")

    # -- Mode & Backend --
    parser.add_argument("--mode", choices=["generative", "extractive"], default="generative",
                        help="Evaluation mode: 'generative' (LLM enabled) or 'extractive' (LLM disabled + fallback)")
    parser.add_argument("--backend", choices=["dense", "bm25"], default="dense",
                        help="Retrieval backend: 'dense' (FAISS) or 'bm25' (Offline/Lite)")
    parser.add_argument("--allow_no_key", action="store_true",
                        help="Allow generative mode without API key (produces LLM_DISABLED). For debug only.")

    args = parser.parse_args()
    cli_args = _json_safe(vars(args))

    # apply external config file if provided
    if args.config:
        import json as _json
        cfg_path = Path(args.config)
        if cfg_path.exists():
            with open(cfg_path) as _f:
                ext_cfg = _json.load(_f)
            for key, val in ext_cfg.items():
                attr = key.upper()
                if hasattr(settings, attr):
                    setattr(settings, attr, val)
                    logger.info(f"Config override: {attr} = {val}")
        else:
            logger.warning(f"Config file not found: {cfg_path}")

    # apply CLI overrides to settings (CLI takes precedence over config file)
    if args.retrieve_k_candidates is not None:
        settings.RETRIEVE_K_CANDIDATES = args.retrieve_k_candidates
    if args.rerank_k_final is not None:
        settings.RERANK_K_FINAL = args.rerank_k_final
    if args.abstain_threshold is not None:
        settings.ABSTAIN_THRESHOLD = args.abstain_threshold
    if args.min_support_rate is not None:
        settings.MIN_SUPPORT_RATE = args.min_support_rate
    if args.enable_llm_verify is not None:
        settings.ENABLE_LLM_VERIFY = args.enable_llm_verify.lower() in ("true", "1", "yes")
    if args.enable_llm_contradictions is not None:
        settings.ENABLE_LLM_CONTRADICTIONS = args.enable_llm_contradictions.lower() in ("true", "1", "yes")

    # --- BACKEND override (if user asked for bm25, or if env forces it) ---
    # We pass 'backend' to run_baseline -> config
    # The actual Retriever instantiation in run_baseline will respect args.backend logic via env? 
    # Better: explicitly pass backend to Retriever if possible, or set env var.
    if args.backend:
        os.environ["POLICY_COPILOT_BACKEND"] = args.backend

    # --- MODE ENFORCEMENT ---
    logger.info(f"=== EVALUATION MODE: {args.mode.upper()} ===")
    logger.info(f"=== RETRIEVAL BACKEND: {args.backend.upper()} ===")

    if args.mode == "extractive":
        settings.ENABLE_LLM = False
        logger.info("Mode is EXTRACTIVE: LLM disabled, fallback enabled.")
    else:
        settings.ENABLE_LLM = True
        logger.info("Mode is GENERATIVE: LLM enabled, fallback disabled.")
        provider = (settings.PROVIDER or "").strip().lower()
        if provider == "openai":
            has_provider_key = bool((settings.OPENAI_API_KEY or "").strip())
            key_hint = "OPENAI_API_KEY"
        elif provider == "anthropic":
            has_provider_key = bool((settings.ANTHROPIC_API_KEY or "").strip())
            key_hint = "ANTHROPIC_API_KEY"
        else:
            has_provider_key = bool((settings.OPENAI_API_KEY or "").strip() or (settings.ANTHROPIC_API_KEY or "").strip())
            key_hint = "OPENAI_API_KEY or ANTHROPIC_API_KEY"
        if not has_provider_key:
            if not args.allow_no_key:
                print(
                    f"ERROR: GENERATIVE mode requires an API key ({key_hint} for provider '{provider or 'unknown'}'). "
                    "Use --allow_no_key only for explicit debug runs.",
                    file=sys.stderr,
                )
                sys.exit(2)
            logger.warning("--allow_no_key: running generative without API key (LLM_DISABLED outputs).")

    def _ablations_for_baseline(bl, a):
        """B2 and B3 need allow_fallback in extractive mode; B3 needs full ablations."""
        base = {"backend": a.backend, "allow_fallback": (a.mode == "extractive")}
        if bl == "b3":
            base.update({
                "no_rerank": a.no_rerank,
                "no_verify": a.no_verify,
                "no_contradictions": a.no_contradictions,
            })
        return base

    if args.baseline == "both":
        baselines_to_run = ["b1", "b2"]
    elif args.baseline == "all":
        baselines_to_run = ["b1", "b2", "b3"]
    else:
        baselines_to_run = [args.baseline]

    for bl in baselines_to_run:
        # Construct deterministic run name
        # Format: {baseline}_{split}_{mode}_{backend}_{timestamp}
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{bl}_{args.split}_{args.mode}_{args.backend}_{ts}"
        if args.run_name:
            name = args.run_name

        logger.info(f"=== Starting {bl.upper()} run: {name} ===")
        run_baseline(bl, args.golden_set, name, force=args.force,
                     ablations=_ablations_for_baseline(bl, args),
                     split=args.split, cli_args=cli_args)


if __name__ == "__main__":
    main()
