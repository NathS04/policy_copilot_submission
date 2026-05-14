"""Replay-score existing runs against the corrected golden set (Phase B).

For each source run directory, copies outputs.jsonl, replaces the
per-record category / is_answerable / gold_paragraph_ids / gold_doc_ids
with values from the corrected golden set, then recomputes summary.json
and tables/metrics.csv by reusing scripts/run_eval.py:_write_summary_metrics.

No LLM calls. No reading of the generated answer text. Pure
re-scoring against new labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]

# (source_run_dir_name, baseline, target_v2_run_dir_name)
# Note: b3_extractive_public_transfer is deliberately excluded — it scores
# against eval/golden_set/public_transfer_set.csv, not the main golden set,
# so the corrected-label audit has no effect on it.
DEFAULT_RUNS = [
    ("b1_generative_final",                  "b1", "b1_generative_v2"),
    ("b2_generative_bm25_fallback_final",    "b2", "b2_generative_v2"),
    ("b3_generative_bm25_fallback_final",    "b3", "b3_generative_v2"),
    ("b3_extractive_final",                  "b3", "b3_extractive_v2"),
]


def load_golden(path: Path) -> dict[str, dict]:
    rows = {}
    with path.open() as f:
        for r in csv.DictReader(f):
            rows[r["query_id"]] = r
    return rows


def load_outputs(path: Path) -> list[dict]:
    recs = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def relabel_record(rec: dict, golden_row: dict) -> dict:
    """Return a new record with labels overwritten from the corrected golden row.
    Other fields (answer, evidence, citations, claim_verification, ...) are preserved.
    """
    new = dict(rec)
    new["category"] = golden_row["category"]
    new["is_answerable"] = golden_row["category"] == "answerable"
    new["gold_paragraph_ids"] = golden_row.get("gold_paragraph_ids", "") or ""
    new["gold_doc_ids"] = golden_row.get("gold_doc_ids", "") or ""
    return new


def write_outputs(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def write_predictions_csv(records: list[dict], path: Path) -> None:
    """Mirror the predictions.csv shape used elsewhere in the project."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "query_id", "category", "question", "answer", "is_abstained",
        "citations", "retrieved_ids_topk",
        "confidence_max", "confidence_mean_top3", "support_rate",
        "unsupported_claims", "contradictions_found",
        "provider", "model", "latency_total_ms", "error",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in records:
            conf = r.get("confidence") or {}
            cv = r.get("claim_verification") or {}
            lat = r.get("latency_ms") or {}
            contradictions = r.get("contradictions") or []
            citations = r.get("citations") or []
            if isinstance(citations, list):
                citations_out = "|".join(citations)
            else:
                citations_out = str(citations)
            retrieved = [e.get("paragraph_id", "") for e in (r.get("evidence") or [])]
            w.writerow({
                "query_id": r.get("query_id", ""),
                "category": r.get("category", ""),
                "question": r.get("question", ""),
                "answer": r.get("answer", ""),
                "is_abstained": r.get("is_abstained", False),
                "citations": citations_out,
                "retrieved_ids_topk": "|".join(retrieved),
                "confidence_max": conf.get("max_rerank", ""),
                "confidence_mean_top3": conf.get("mean_top3_rerank", ""),
                "support_rate": cv.get("support_rate", "") if isinstance(cv, dict) else "",
                "unsupported_claims": cv.get("unsupported_claims", "") if isinstance(cv, dict) else "",
                "contradictions_found": len(contradictions),
                "provider": r.get("provider", ""),
                "model": r.get("model", ""),
                "latency_total_ms": sum(lat.values()) if isinstance(lat, dict) else "",
                "error": "",
            })


def replay_one(
    src_run: Path,
    dst_run: Path,
    golden: dict[str, dict],
    baseline: str,
    source_run_name: str,
    write_summary_metrics_fn,
) -> dict:
    """Replay a single source run against the corrected golden set."""
    src_outputs = src_run / "outputs.jsonl"
    src_config = src_run / "run_config.json"
    if not src_outputs.exists():
        raise SystemExit(f"missing {src_outputs}")
    if not src_config.exists():
        raise SystemExit(f"missing {src_config}")

    dst_run.mkdir(parents=True, exist_ok=True)

    # 1. copy + augment run_config.json with replay provenance.
    cfg = json.loads(src_config.read_text())
    cfg["dataset_version"] = "golden_set_v2_corrected"
    cfg["replay_provenance"] = {
        "replayed_from": source_run_name,
        "replayed_at": datetime.now(timezone.utc).isoformat(),
        "replay_script": "scripts/replay_score_runs.py",
        "no_llm_calls": True,
    }
    (dst_run / "run_config.json").write_text(json.dumps(cfg, indent=2) + "\n")

    # 2. relabel outputs.jsonl
    records = load_outputs(src_outputs)
    relabelled = []
    missing_golden = []
    for rec in records:
        qid = rec.get("query_id")
        if qid not in golden:
            missing_golden.append(qid)
            relabelled.append(rec)
            continue
        relabelled.append(relabel_record(rec, golden[qid]))
    if missing_golden:
        raise SystemExit(
            f"replay aborted: query_ids in source {source_run_name} have no row in "
            f"corrected golden set: {missing_golden}"
        )

    write_outputs(relabelled, dst_run / "outputs.jsonl")
    write_predictions_csv(relabelled, dst_run / "predictions.csv")

    # 3. recompute summary.json + tables/metrics.csv
    write_summary_metrics_fn(dst_run, relabelled, baseline)

    # README
    (dst_run / "README.md").write_text(
        f"# {dst_run.name}\n\n"
        f"Replay of `{source_run_name}` against `golden_set_v2_corrected.csv`.\n"
        f"No LLM calls. Generated by `scripts/replay_score_runs.py`.\n"
    )

    summary = json.loads((dst_run / "summary.json").read_text())
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, default=ROOT / "results/runs")
    parser.add_argument("--golden-set", type=Path,
                        default=ROOT / "eval/golden_set/golden_set_v2_corrected.csv")
    args = parser.parse_args()

    # Import the canonical metric-writer to ensure replay matches the
    # existing scoring code byte-for-byte.
    sys.path.insert(0, str(ROOT))
    try:
        from scripts.run_eval import _write_summary_metrics
    finally:
        sys.path.pop(0)

    golden = load_golden(args.golden_set)
    print(f"Loaded {len(golden)} rows from {args.golden_set.name}")

    for src_name, baseline, dst_name in DEFAULT_RUNS:
        src_run = args.runs_root / src_name
        dst_run = args.runs_root / dst_name
        if not src_run.exists():
            print(f"SKIP: source run {src_run} not present.")
            continue
        summary = replay_one(
            src_run, dst_run, golden, baseline, src_name, _write_summary_metrics
        )
        # Show key metrics so we can compare against the old summary, if present.
        old_summary_path = src_run / "summary.json"
        old = json.loads(old_summary_path.read_text()) if old_summary_path.exists() else {}
        print(f"\n=== {src_name} -> {dst_name} (baseline={baseline}) ===")
        for key in (
            "total_queries", "answer_rate", "abstention_accuracy",
            "evidence_recall_at_5", "evidence_mrr",
            "citation_precision", "citation_recall",
            "ungrounded_rate", "support_rate_mean",
            "contradiction_recall", "contradiction_precision",
        ):
            o = old.get(key, "—")
            n = summary.get(key, "—")
            arrow = "" if o == n else "  *changed*"
            print(f"  {key:>28}: {o!s:>10} -> {n!s:>10}{arrow}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
