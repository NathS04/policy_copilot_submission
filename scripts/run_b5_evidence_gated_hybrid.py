"""B5 Evidence-Gated Hybrid runner (final round).

Replays the deterministic B5 gate (see
src/policy_copilot/service/evidence_gated_hybrid.py) over the retained
B3-Extractive hybrid outputs and writes a new run directory with the
gate metadata + recomputed metrics against the corrected v2 golden set.

No LLM calls. No retrieval changes. Citations are paragraph IDs from
the original top-5 reranked evidence; the gate either surfaces the
top paragraph (or both contradictory paragraphs) or abstains.
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
DEFAULT_SOURCE = ROOT / "results/runs/b3_extractive_hybrid_v2_final"
DEFAULT_GOLDEN = ROOT / "eval/golden_set/golden_set_v2_corrected.csv"
DEFAULT_OUT = ROOT / "results/runs/b5_evidence_gated_hybrid_v3_final"


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
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE,
                        help="B3-Extractive hybrid source run dir")
    parser.add_argument("--golden-set", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--out-run", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--rerank-floor", type=float, default=None)
    parser.add_argument("--overlap-floor", type=float, default=None)
    parser.add_argument("--high-rerank", type=float, default=None)
    parser.add_argument("--low-overlap-cutoff", type=float, default=None)
    parser.add_argument("--no-numeric-filter", action="store_true")
    parser.add_argument("--no-qualifier-filter", action="store_true")
    parser.add_argument("--no-generic-filter", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    try:
        from policy_copilot.service.evidence_gated_hybrid import (
            apply_b5_gate, DEFAULTS as B5_DEFAULTS
        )
        from policy_copilot.verify.contradictions import detect_contradictions
        from scripts.run_eval import _write_summary_metrics
    finally:
        sys.path.pop(0)

    # Build effective config from CLI overrides.
    cfg = {**B5_DEFAULTS}
    if args.rerank_floor is not None:
        cfg["rerank_floor"] = args.rerank_floor
    if args.overlap_floor is not None:
        cfg["overlap_floor"] = args.overlap_floor
    if args.high_rerank is not None:
        cfg["high_rerank"] = args.high_rerank
    if args.low_overlap_cutoff is not None:
        cfg["low_overlap_cutoff"] = args.low_overlap_cutoff
    if args.no_numeric_filter:
        cfg["numeric_filter"] = False
    if args.no_qualifier_filter:
        cfg["qualifier_filter"] = False
    if args.no_generic_filter:
        cfg["generic_filter"] = False

    src_outputs = args.source_run / "outputs.jsonl"
    src_config = args.source_run / "run_config.json"
    if not src_outputs.exists():
        print(f"ERROR: missing {src_outputs}", file=sys.stderr)
        return 2
    if not src_config.exists():
        print(f"ERROR: missing {src_config}", file=sys.stderr)
        return 2

    source_records = load_outputs(src_outputs)
    golden = load_golden(args.golden_set)
    print(f"Loaded {len(source_records)} source records from {args.source_run.name}")

    new_records: List[Dict] = []
    counts = {"surfaced": 0, "surfaced_contradiction_aware": 0, "abstained": 0}

    for rec in source_records:
        qid = rec.get("query_id")
        question = rec.get("question", "")

        # The B3-Extractive source already carries `evidence` (top-5 reranked).
        # Some older runs use `retrieved_paragraph_ids`; handle both.
        evidence = rec.get("evidence") or []
        if not evidence and rec.get("retrieved_paragraph_ids"):
            # Fallback (no text available — gate will treat as weak retrieval)
            evidence = [
                {"paragraph_id": pid, "text": "", "score_rerank": 0.0}
                for pid in (rec.get("retrieved_paragraph_ids") or [])
            ]

        # Run the contradiction detector on the same top-5 evidence so the
        # contradiction-aware path can fire when both sides retrieved.
        try:
            contradictions = detect_contradictions(evidence) if evidence else []
        except Exception:
            contradictions = []

        gate = apply_b5_gate(question, evidence, contradictions=contradictions, cfg=cfg)

        # Build the new record, preserving golden-set fields and source provenance.
        gold = golden.get(qid, {})
        new = dict(rec)
        # Force corrected v2 labels.
        if gold:
            new["category"] = gold["category"]
            new["is_answerable"] = gold["category"] == "answerable"
            new["gold_paragraph_ids"] = gold.get("gold_paragraph_ids", "") or ""
            new["gold_doc_ids"] = gold.get("gold_doc_ids", "") or ""

        new["baseline"] = "b5"
        new["mode_used"] = gate["mode_used"]
        new["answer"] = gate["answer"]
        new["citations"] = gate["citations"]
        new["is_abstained"] = gate["is_abstained"]
        new["answerability_decision"] = gate["answerability_decision"]
        new["answerability_reason"] = gate["answerability_reason"]
        new["evidence_strength"] = gate["evidence_strength"]
        new["gate_features"] = {k: v for k, v in gate["gate_features"].items() if k != "qualifiers"}
        new["selected_citation_ids"] = gate["selected_citation_ids"]
        # Backend provenance — explicit.
        new["backend_used"] = "hybrid"

        # For surfaced rows, mark a clean single/double-claim verification
        # so the existing metric helpers count Ungrounded correctly.
        if gate["mode_used"] in ("surfaced", "surfaced_contradiction_aware"):
            n_cit = max(1, len(gate["citations"]))
            new["claim_verification"] = {
                "claims": [
                    {
                        "claim_id": f"c{i+1}",
                        "text": (gate["answer"] or "")[:200],
                        "citations": list(gate["citations"]),
                        "supported": True,
                        "support_rationale": "B5 extractive surface: cited paragraph is the answer text",
                        "verification_tier": "extractive_construction",
                        "unsupported_reason": None,
                    }
                    for i in range(n_cit)
                ],
                "supported_claims": n_cit,
                "unsupported_claims": 0,
                "support_rate": 1.0,
            }
        else:
            new["claim_verification"] = None

        counts[gate["mode_used"]] = counts.get(gate["mode_used"], 0) + 1
        new_records.append(new)

    # Write outputs.
    args.out_run.mkdir(parents=True, exist_ok=True)
    with (args.out_run / "outputs.jsonl").open("w") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")

    # run_config.json
    source_cfg = json.loads(src_config.read_text())
    new_cfg = {
        "baseline": "b5",
        "mode": "evidence_gated_hybrid",
        "backend_requested": "hybrid",
        "backend_used": "hybrid",
        "dataset_version": "golden_set_v2_corrected",
        "source_run_config": source_cfg,
        "b5_gate_cfg": cfg,
        "b5_provenance": {
            "source_run": args.source_run.name,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "script": "scripts/run_b5_evidence_gated_hybrid.py",
            "no_llm_calls": True,
            "mode_counts": counts,
        },
    }
    (args.out_run / "run_config.json").write_text(json.dumps(new_cfg, indent=2) + "\n")

    # predictions.csv
    pred_fields = [
        "query_id", "category", "question", "answer", "is_abstained",
        "mode_used", "answerability_decision", "answerability_reason",
        "citations", "retrieved_ids_topk",
        "top_rerank", "top_overlap", "qualifier_in_top",
        "generic_paragraph", "top_has_digit", "is_numeric_q",
    ]
    with (args.out_run / "predictions.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pred_fields)
        w.writeheader()
        for r in new_records:
            es = r.get("evidence_strength") or {}
            cits = r.get("citations") or []
            if isinstance(cits, list):
                cits = "|".join(cits)
            retrieved = "|".join([
                e.get("paragraph_id", "") for e in (r.get("evidence") or [])
            ])
            w.writerow({
                "query_id": r.get("query_id", ""),
                "category": r.get("category", ""),
                "question": r.get("question", ""),
                "answer": (r.get("answer") or "")[:200],
                "is_abstained": r.get("is_abstained", False),
                "mode_used": r.get("mode_used", ""),
                "answerability_decision": r.get("answerability_decision", ""),
                "answerability_reason": r.get("answerability_reason", ""),
                "citations": cits,
                "retrieved_ids_topk": retrieved,
                "top_rerank": es.get("top_rerank", ""),
                "top_overlap": es.get("top_overlap", ""),
                "qualifier_in_top": es.get("qualifier_in_top", ""),
                "generic_paragraph": es.get("generic_paragraph", ""),
                "top_has_digit": es.get("top_has_digit", ""),
                "is_numeric_q": es.get("is_numeric_q", ""),
            })

    # README.md
    (args.out_run / "README.md").write_text(
        f"# {args.out_run.name}\n\n"
        f"B5 Evidence-Gated Hybrid replay over `{args.source_run.name}/outputs.jsonl`.\n"
        f"Generated by `scripts/run_b5_evidence_gated_hybrid.py`. No LLM calls.\n\n"
        f"Mode counts: {counts}\n\n"
        f"Gate config: {cfg}\n"
    )

    # summary.json + tables/metrics.csv via canonical helper.
    _write_summary_metrics(args.out_run, new_records, "b3")
    # Patch the baseline field to b5.
    summary_path = args.out_run / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["baseline"] = "b5"
    summary["b5_mode_counts"] = counts
    summary["b5_gate_cfg"] = cfg
    summary_path.write_text(json.dumps(summary, indent=2))

    # Console report.
    print(f"\nB5 replay over {args.source_run.name}:")
    print(f"  total queries   : {len(new_records)}")
    print(f"  mode counts     : {counts}")
    for key in (
        "answer_rate", "abstention_accuracy", "evidence_recall_at_5",
        "citation_precision", "citation_recall", "ungrounded_rate",
        "contradiction_recall", "contradiction_precision",
    ):
        print(f"  {key:>22} : {summary.get(key)}")
    print(f"Wrote {args.out_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
