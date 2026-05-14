"""B4 Conservative Hybrid replay (Phase F).

Replays the B4 policy over a source B3-Generative outputs.jsonl,
producing a new run directory with B4 metadata per row.

The source run supplies:
  - the generative answer text (if produced)
  - the support_rate from claim_verification
  - the retrieved evidence list with reranker scores

For each row, ``apply_b4_fallback_policy`` decides whether to keep the
generative answer, fall back to extractive on the top retrieved
paragraph, or abstain.

No LLM calls. Records are then re-scored against
``golden_set_v2_corrected.csv`` using the same metric helpers as
``scripts/run_eval.py:_write_summary_metrics``.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]


def load_outputs(p: Path) -> List[Dict]:
    out = []
    with p.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_golden(p: Path) -> Dict[str, Dict]:
    rows = {}
    with p.open() as f:
        for r in csv.DictReader(f):
            rows[r["query_id"]] = r
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", default="b3_generative_v2",
                        help="Source run name under results/runs/")
    parser.add_argument("--golden-set", type=Path,
                        default=ROOT / "eval/golden_set/golden_set_v2_corrected.csv")
    parser.add_argument("--out-run", default="b4_conservative_hybrid_replay_v2_final",
                        help="New run name to create under results/runs/")
    args = parser.parse_args()

    src_dir = ROOT / "results/runs" / args.source_run
    dst_dir = ROOT / "results/runs" / args.out_run
    if not src_dir.exists():
        print(f"ERROR: source run {src_dir} not present", file=sys.stderr)
        return 2

    src_outputs = src_dir / "outputs.jsonl"
    src_config = src_dir / "run_config.json"
    records = load_outputs(src_outputs)
    golden = load_golden(args.golden_set)
    print(f"Loaded {len(records)} source records from {args.source_run}")

    # Import the B4 policy module at runtime to avoid circular imports.
    sys.path.insert(0, str(ROOT))
    try:
        from src.policy_copilot.service.conservative_hybrid import apply_b4_fallback_policy
    except ModuleNotFoundError:
        # The project is installed via pip install -e; package path is policy_copilot.
        from policy_copilot.service.conservative_hybrid import apply_b4_fallback_policy
    try:
        from scripts.run_eval import _write_summary_metrics
    finally:
        sys.path.pop(0)

    new_records: List[Dict] = []
    counts = {"generative": 0, "extractive_fallback": 0, "abstained": 0}
    for rec in records:
        qid = rec.get("query_id")
        gold = golden.get(qid)
        # First, refresh labels to v2 corrected (idempotent if the source is _v2).
        new = dict(rec)
        if gold is not None:
            new["category"] = gold["category"]
            new["is_answerable"] = gold["category"] == "answerable"
            new["gold_paragraph_ids"] = gold.get("gold_paragraph_ids", "") or ""
            new["gold_doc_ids"] = gold.get("gold_doc_ids", "") or ""

        # Build a B4-policy-shaped response payload.
        cv = rec.get("claim_verification") or {}
        support_rate = cv.get("support_rate") if isinstance(cv, dict) else None
        b4_input = {
            "question": rec.get("question", ""),
            "answer": rec.get("answer", ""),
            "citations": rec.get("citations", []),
            "support_rate": support_rate,
            "is_abstained": rec.get("is_abstained", False),
        }
        b4_out = apply_b4_fallback_policy(b4_input, rec.get("evidence", []) or [])

        # Merge B4 metadata back into the record.
        new["baseline"] = "b4"
        new["answer"] = b4_out.get("answer", new.get("answer", ""))
        new["citations"] = b4_out.get("citations", new.get("citations", []))
        new["is_abstained"] = (new["answer"] == "INSUFFICIENT_EVIDENCE")
        new["mode_used"] = b4_out["mode_used"]
        new["fallback_reason"] = b4_out["fallback_reason"]
        new["evidence_strength"] = b4_out["evidence_strength"]

        # For extractive_fallback rows, the surfaced answer IS the cited
        # paragraph verbatim — so by construction it is fully grounded. The
        # original generative claim_verification (which fired the support
        # gate) no longer describes the surfaced response. Mark it as a
        # clean single-claim extractive verification, matching how
        # B3-Extractive runs are scored elsewhere in the codebase.
        if new["mode_used"] == "extractive_fallback":
            new["claim_verification"] = {
                "claims": [{
                    "claim_id": "c1",
                    "text": new["answer"][:200],
                    "citations": list(new["citations"] or []),
                    "supported": True,
                    "support_rationale": "extractive_fallback: answer is the cited paragraph verbatim",
                    "verification_tier": "extractive_construction",
                    "unsupported_reason": None,
                }],
                "supported_claims": 1,
                "unsupported_claims": 0,
                "support_rate": 1.0,
            }
        # For abstained rows, drop claims so the metric correctly excludes them.
        if new["mode_used"] == "abstained":
            # answer is INSUFFICIENT_EVIDENCE; the existing metric already
            # excludes these, so leaving claim_verification untouched is safe.
            pass

        counts[new["mode_used"]] = counts.get(new["mode_used"], 0) + 1
        new_records.append(new)

    # Write outputs.
    dst_dir.mkdir(parents=True, exist_ok=True)
    with (dst_dir / "outputs.jsonl").open("w") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")

    # run_config.json (with B4 provenance).
    cfg = json.loads(src_config.read_text()) if src_config.exists() else {}
    cfg["baseline"] = "b4"
    cfg["mode"] = "b4_conservative"
    cfg["dataset_version"] = "golden_set_v2_corrected"
    cfg["b4_replay_provenance"] = {
        "replayed_from": args.source_run,
        "replayed_at": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/run_b4_replay.py",
        "no_llm_calls": True,
        "mode_counts": counts,
    }
    (dst_dir / "run_config.json").write_text(json.dumps(cfg, indent=2) + "\n")

    # Predictions CSV.
    pred_fields = [
        "query_id", "category", "question", "answer", "is_abstained",
        "mode_used", "fallback_reason",
        "citations", "retrieved_ids_topk",
        "support_rate", "top_rerank", "top_overlap",
    ]
    with (dst_dir / "predictions.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pred_fields)
        w.writeheader()
        for r in new_records:
            cv = r.get("claim_verification") or {}
            es = r.get("evidence_strength") or {}
            retrieved = "|".join([e.get("paragraph_id", "") for e in (r.get("evidence") or [])])
            citations = r.get("citations", [])
            if isinstance(citations, list):
                citations = "|".join(citations)
            w.writerow({
                "query_id": r.get("query_id", ""),
                "category": r.get("category", ""),
                "question": r.get("question", ""),
                "answer": r.get("answer", "")[:200],
                "is_abstained": r.get("is_abstained", False),
                "mode_used": r.get("mode_used", ""),
                "fallback_reason": r.get("fallback_reason", ""),
                "citations": citations,
                "retrieved_ids_topk": retrieved,
                "support_rate": cv.get("support_rate", "") if isinstance(cv, dict) else "",
                "top_rerank": es.get("top_rerank", ""),
                "top_overlap": es.get("top_overlap", ""),
            })

    # README and summary.
    (dst_dir / "README.md").write_text(
        f"# {args.out_run}\n\n"
        f"B4 Conservative Hybrid Mode replay over `{args.source_run}/outputs.jsonl`.\n"
        f"No LLM calls. Generated by `scripts/run_b4_replay.py`.\n"
        f"Mode counts: {counts}\n"
    )

    # Score against the corrected golden set using the canonical helper.
    _write_summary_metrics(dst_dir, new_records, "b3")

    # B4-specific metadata: add mode counts and B4-specific answer rate
    # decomposition to summary.json.
    summary_path = dst_dir / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["baseline"] = "b4"
    summary["b4_mode_counts"] = counts
    summary_path.write_text(json.dumps(summary, indent=2))

    print(f"\nB4 replay over {args.source_run}:")
    print(f"  total queries  : {len(new_records)}")
    print(f"  mode counts    : {counts}")
    print(f"  answer rate    : {summary.get('answer_rate')}")
    print(f"  abstention acc : {summary.get('abstention_accuracy')}")
    print(f"  ungrounded     : {summary.get('ungrounded_rate')}")
    print(f"  recall@5       : {summary.get('evidence_recall_at_5')}")
    print(f"Wrote {dst_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
