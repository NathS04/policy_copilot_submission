"""Replay the abstention gate at a sweep of thresholds.

The B3 system has two abstention knobs:

  1. Pre-LLM ``abstain_threshold`` against the cross-encoder reranker
     score. In every shipped run this is fixed at 0.30, but the
     reranker score is saturated at 1.0 because the dense backend
     could not be loaded and the system falls back to BM25 with a
     normalised top-1 score of 1.0 (see §3.3 in the report). The
     pre-LLM gate therefore does not fire on any record in the
     current evaluation runs.

  2. Post-LLM ``min_support_rate`` against the per-claim verification
     output. In the shipped run this is fixed at 0.80. Any response
     whose verified support rate falls below this threshold is
     downgraded to ``INSUFFICIENT_EVIDENCE`` regardless of what the
     LLM produced. This is the gate that does the real abstention
     work in the system as deployed.

This script replays both gates from the per-record data already
stored in ``outputs.jsonl`` (no LLM calls). For each row in the
sweep CSV we record what the gate would have produced at a given
support-rate threshold, holding the pre-LLM threshold at its
shipped value of 0.30. This is the curve that should appear in
Figure 4.4 — it shows the actual coverage / quality trade-off the
system would have exhibited under a different support-rate cutoff.

Output: ``results/tables/threshold_sweep.csv`` with columns

    scope, support_threshold,
    coverage, abstention_accuracy, answerable_recall,
    abstention_precision, abstention_f1,
    n_total, n_answered, n_abstained.

Scope is one of ``all``, ``test``, ``dev``.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


REFUSAL_CATEGORIES = {"unanswerable", "contradiction"}
PRE_LLM_THRESHOLD = 0.30  # fixed at the shipped value


def load_records(jsonl_path: Path) -> list[dict]:
    records: list[dict] = []
    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_split_map(golden_csv: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with golden_csv.open() as f:
        for row in csv.DictReader(f):
            mapping[row["query_id"]] = row.get("split", "")
    return mapping


def replay_decision(record: dict, support_threshold: float) -> bool:
    """Return True if the record would be answered (NOT abstained) at
    the given support-rate threshold, holding the pre-LLM threshold at
    its shipped value of 0.30."""
    conf = record.get("confidence") or {}
    max_rerank = float(conf.get("max_rerank", 0.0))
    if max_rerank < PRE_LLM_THRESHOLD:
        return False  # pre-LLM gate fired

    cv = record.get("claim_verification")
    if not isinstance(cv, dict):
        # LLM produced no verifiable claims (e.g. it refused outright)
        # — treat as abstain.
        return False

    rate = cv.get("support_rate")
    if rate is None:
        # No claims to verify — also treated as abstain.
        return False

    return float(rate) >= support_threshold


def metrics_at(records: Iterable[dict], support_threshold: float) -> dict[str, float]:
    rs = list(records)
    if not rs:
        return {}
    pass_gate = [replay_decision(r, support_threshold) for r in rs]
    cats = [r["category"] for r in rs]

    n_total = len(rs)
    n_answered = sum(pass_gate)
    n_abstained = n_total - n_answered

    # Per-category counts -- the report defines abstention_accuracy on the
    # unanswerable subset only and reports contradiction_recall separately,
    # so we mirror that here rather than collapsing both into one number.
    n_answerable = sum(c == "answerable" for c in cats)
    n_unanswerable = sum(c == "unanswerable" for c in cats)
    n_contradiction = sum(c == "contradiction" for c in cats)

    unanswerable_abstained = sum(
        (c == "unanswerable") and (not pg) for c, pg in zip(cats, pass_gate)
    )
    contradiction_abstained = sum(
        (c == "contradiction") and (not pg) for c, pg in zip(cats, pass_gate)
    )
    answerable_answered = sum(
        (c == "answerable") and pg for c, pg in zip(cats, pass_gate)
    )

    refusal_gold = [c in REFUSAL_CATEGORIES for c in cats]
    tp = sum(rg and (not pg) for rg, pg in zip(refusal_gold, pass_gate))
    fp = sum((not rg) and (not pg) for rg, pg in zip(refusal_gold, pass_gate))
    fn = sum(rg and pg for rg, pg in zip(refusal_gold, pass_gate))

    coverage = n_answered / n_total
    # answer_rate matches the report's Table 4.2 definition:
    #   answer_rate = (answerable queries the system answers) / (answerable queries)
    answer_rate = (
        answerable_answered / n_answerable
    ) if n_answerable else float("nan")
    abstention_accuracy = (
        unanswerable_abstained / n_unanswerable
    ) if n_unanswerable else float("nan")
    contradiction_abstain_rate = (
        contradiction_abstained / n_contradiction
    ) if n_contradiction else float("nan")
    refusal_f1 = (
        (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) else float("nan")
    )

    return {
        "n_total": n_total,
        "n_answered": n_answered,
        "n_abstained": n_abstained,
        "coverage": round(coverage, 4),
        "answer_rate": round(answer_rate, 4),
        "abstention_accuracy": round(abstention_accuracy, 4),
        "contradiction_abstain_rate": round(contradiction_abstain_rate, 4),
        "refusal_f1": round(refusal_f1, 4),
    }


def sweep(
    records: list[dict],
    thresholds: list[float],
    split_map: dict[str, str] | None = None,
) -> list[dict]:
    rows: list[dict] = []
    for tau in thresholds:
        m = metrics_at(records, tau)
        m.update({"support_threshold": round(tau, 4), "scope": "all"})
        rows.append(m)
        if split_map:
            for split_name in ("test", "dev"):
                subset = [
                    r for r in records
                    if split_map.get(r["query_id"], "") == split_name
                ]
                if subset:
                    m = metrics_at(subset, tau)
                    m.update({"support_threshold": round(tau, 4), "scope": split_name})
                    rows.append(m)
    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "scope", "support_threshold",
        "coverage", "answer_rate",
        "abstention_accuracy", "contradiction_abstain_rate", "refusal_f1",
        "n_total", "n_answered", "n_abstained",
    ]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--run",
        default="results/runs/b3_generative_bm25_fallback_final",
        help="Path to the run directory containing outputs.jsonl",
    )
    p.add_argument(
        "--golden",
        default="eval/golden_set/golden_set.csv",
        help="Golden-set CSV (used only for the test/dev split breakdown)",
    )
    p.add_argument(
        "--out",
        default="results/tables/threshold_sweep.csv",
    )
    p.add_argument("--start", type=float, default=0.00)
    p.add_argument("--stop", type=float, default=1.00)
    p.add_argument("--step", type=float, default=0.05)
    args = p.parse_args()

    run_dir = Path(args.run)
    jsonl = run_dir / "outputs.jsonl"
    if not jsonl.exists():
        raise SystemExit(f"Missing {jsonl}")

    records = load_records(jsonl)
    print(f"Loaded {len(records)} records from {jsonl}")

    split_map: dict[str, str] | None = None
    golden = Path(args.golden)
    if golden.exists():
        split_map = load_split_map(golden)
        n_test = sum(1 for v in split_map.values() if v == "test")
        n_dev = sum(1 for v in split_map.values() if v == "dev")
        print(f"Loaded split map: {n_test} test / {n_dev} dev")

    n_steps = int(round((args.stop - args.start) / args.step)) + 1
    thresholds = [round(args.start + i * args.step, 4) for i in range(n_steps)]
    # Always include the shipped operating point (0.80 support-rate).
    if 0.80 not in thresholds:
        thresholds.append(0.80)
    thresholds = sorted(set(thresholds))

    rows = sweep(records, thresholds, split_map)
    write_csv(rows, Path(args.out))

    print(f"Wrote {len(rows)} rows to {args.out}")

    for scope in ("all", "test"):
        chosen = next(
            (r for r in rows if r["scope"] == scope and r["support_threshold"] == 0.80),
            None,
        )
        if chosen:
            print(
                f"  {scope}/0.80 -> coverage={chosen['coverage']:.3f}, "
                f"answer_rate={chosen['answer_rate']:.3f}, "
                f"abstention_accuracy={chosen['abstention_accuracy']:.3f}, "
                f"refusal_f1={chosen['refusal_f1']:.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
