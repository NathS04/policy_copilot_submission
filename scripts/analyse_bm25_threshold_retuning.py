"""BM25-specific threshold retuning diagnostic.

Replays the post-LLM support-rate gate over the retained B3-Generative
outputs at fine-grained tau, adding a per-tau response-level Ungrounded
Rate column that the original `scripts/sweep_abstention.py` does not
compute, and selecting a single retuned operating point under explicit
safety constraints.

Selection rule (frozen):

    argmax_tau  answer_rate
    subject to  abstention_accuracy >= 0.80
                ungrounded_rate_response <= 0.05
                n_answered >= 1

Tie-breakers: higher abstention_accuracy, lower ungrounded_rate, higher tau.

This script makes no LLM/API calls. It reads the existing retained
artefacts and reuses the gate semantics already implemented in
`scripts/sweep_abstention.py:replay_decision`.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


PRE_LLM_THRESHOLD = 0.30  # same value used by scripts/sweep_abstention.py
SHIPPED_TAU = 0.80

ABSTENTION_ACCURACY_MIN = 0.80
UNGROUNDED_RATE_MAX = 0.05

# Tolerance for cross-checking against summary.json (gate G1).
ANSWER_RATE_TOL = 0.01
ABSTENTION_ACC_TOL = 0.01


def load_records(jsonl_path: Path) -> list[dict]:
    records: list[dict] = []
    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_golden(csv_path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            rows[row["query_id"]] = row
    return rows


def replay_decision(record: dict, support_threshold: float) -> bool:
    """Mirror of scripts/sweep_abstention.py:replay_decision.

    True iff the record would be surfaced (NOT abstained) at the given
    post-LLM support-rate threshold, holding the pre-LLM threshold at
    its shipped value of 0.30."""
    conf = record.get("confidence") or {}
    max_rerank = float(conf.get("max_rerank", 0.0))
    if max_rerank < PRE_LLM_THRESHOLD:
        return False
    cv = record.get("claim_verification")
    if not isinstance(cv, dict):
        return False
    rate = cv.get("support_rate")
    if rate is None:
        return False
    return float(rate) >= support_threshold


def is_response_ungrounded(record: dict) -> bool:
    """Response-level ungrounded: at least one unsupported claim.

    Uses the same heuristic verifier output stored in
    record['claim_verification']['unsupported_claims']."""
    cv = record.get("claim_verification")
    if not isinstance(cv, dict):
        return False
    return int(cv.get("unsupported_claims") or 0) > 0


def metrics_at(records: list[dict], tau: float) -> dict:
    pass_gate = [replay_decision(r, tau) for r in records]
    cats = [r["category"] for r in records]

    n_total = len(records)
    n_answered = sum(pass_gate)
    n_abstained = n_total - n_answered

    n_answerable = sum(c == "answerable" for c in cats)
    n_unanswerable = sum(c == "unanswerable" for c in cats)
    n_contradiction = sum(c == "contradiction" for c in cats)

    answerable_answered = sum(
        (c == "answerable") and pg for c, pg in zip(cats, pass_gate)
    )
    unanswerable_abstained = sum(
        (c == "unanswerable") and (not pg) for c, pg in zip(cats, pass_gate)
    )
    contradiction_abstained = sum(
        (c == "contradiction") and (not pg) for c, pg in zip(cats, pass_gate)
    )

    surfaced = [r for r, pg in zip(records, pass_gate) if pg]
    n_ungrounded_surfaced = sum(is_response_ungrounded(r) for r in surfaced)

    answer_rate = answerable_answered / n_answerable if n_answerable else float("nan")
    abstention_accuracy = (
        unanswerable_abstained / n_unanswerable if n_unanswerable else float("nan")
    )
    contradiction_abstain_rate = (
        contradiction_abstained / n_contradiction if n_contradiction else float("nan")
    )
    coverage_all = n_answered / n_total if n_total else float("nan")
    if surfaced:
        ungrounded_rate_response = n_ungrounded_surfaced / len(surfaced)
        support_rate_mean_surfaced = sum(
            float(r["claim_verification"]["support_rate"]) for r in surfaced
        ) / len(surfaced)
    else:
        ungrounded_rate_response = 0.0
        support_rate_mean_surfaced = float("nan")

    return {
        "tau": round(tau, 4),
        "answer_rate": round(answer_rate, 4),
        "abstention_accuracy": round(abstention_accuracy, 4),
        "ungrounded_rate_response": round(ungrounded_rate_response, 4),
        "contradiction_abstain_rate": round(contradiction_abstain_rate, 4),
        "coverage_all": round(coverage_all, 4),
        "n_total": n_total,
        "n_answered": n_answered,
        "n_abstained": n_abstained,
        "n_answerable": n_answerable,
        "n_unanswerable": n_unanswerable,
        "n_contradiction": n_contradiction,
        "n_surfaced_total": len(surfaced),
        "n_surfaced_ungrounded": n_ungrounded_surfaced,
        "support_rate_mean_surfaced": (
            round(support_rate_mean_surfaced, 4)
            if surfaced and support_rate_mean_surfaced == support_rate_mean_surfaced
            else ""
        ),
    }


def select_operating_point(sweep_rows: list[dict]) -> tuple[dict | None, str]:
    """Apply the selection rule. Returns (selected_row, interpretation)."""
    feasible = [
        r for r in sweep_rows
        if r["abstention_accuracy"] >= ABSTENTION_ACCURACY_MIN
        and r["ungrounded_rate_response"] <= UNGROUNDED_RATE_MAX
        and r["n_answered"] >= 1
    ]
    if feasible:
        feasible.sort(
            key=lambda r: (
                -r["answer_rate"],
                -r["abstention_accuracy"],
                r["ungrounded_rate_response"],
                -r["tau"],
            )
        )
        return feasible[0], "balanced_point_meets_constraints"

    # No feasible point. Try a diagnostic that keeps Ungrounded safe.
    ungrounded_safe = [
        r for r in sweep_rows
        if r["ungrounded_rate_response"] <= UNGROUNDED_RATE_MAX
        and r["n_answered"] >= 1
    ]
    if ungrounded_safe:
        ungrounded_safe.sort(
            key=lambda r: (
                -r["answer_rate"],
                -r["abstention_accuracy"],
                r["ungrounded_rate_response"],
                -r["tau"],
            )
        )
        return ungrounded_safe[0], "diagnostic_point_only"

    return None, "no_safe_retuned_point"


def validate_against_summary(
    conservative_row: dict, summary: dict
) -> tuple[bool, list[str]]:
    """Gate G1: conservative point must reproduce summary.json values."""
    issues: list[str] = []
    ar = summary.get("answer_rate")
    aa = summary.get("abstention_accuracy")
    ur = summary.get("ungrounded_rate")
    if ar is None or abs(conservative_row["answer_rate"] - float(ar)) > ANSWER_RATE_TOL:
        issues.append(
            f"answer_rate mismatch: reconstructed={conservative_row['answer_rate']} "
            f"vs summary.json={ar} (tol={ANSWER_RATE_TOL})"
        )
    if aa is None or abs(
        conservative_row["abstention_accuracy"] - float(aa)
    ) > ABSTENTION_ACC_TOL:
        issues.append(
            f"abstention_accuracy mismatch: reconstructed="
            f"{conservative_row['abstention_accuracy']} vs summary.json={aa} "
            f"(tol={ABSTENTION_ACC_TOL})"
        )
    if ur is None or abs(
        conservative_row["ungrounded_rate_response"] - float(ur)
    ) > 1e-6:
        issues.append(
            f"ungrounded_rate_response mismatch: reconstructed="
            f"{conservative_row['ungrounded_rate_response']} "
            f"vs summary.json={ur} (must be exactly equal)"
        )
    return (not issues), issues


def check_required_fields(records: list[dict]) -> list[str]:
    """Returns a list of human-readable problems with the inputs."""
    problems: list[str] = []
    needed_in_answered = ("claim_verification",)
    for r in records:
        if "category" not in r:
            problems.append(f"{r.get('query_id')}: missing 'category'")
        if "confidence" not in r:
            problems.append(f"{r.get('query_id')}: missing 'confidence'")
    return problems


def thresholds(step: float) -> list[float]:
    n = int(round(1.0 / step)) + 1
    out = [round(i * step, 4) for i in range(n)]
    if SHIPPED_TAU not in out:
        out.append(SHIPPED_TAU)
    return sorted(set(out))


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "tau",
        "answer_rate",
        "abstention_accuracy",
        "ungrounded_rate_response",
        "contradiction_abstain_rate",
        "coverage_all",
        "n_total",
        "n_answered",
        "n_abstained",
        "n_answerable",
        "n_unanswerable",
        "n_contradiction",
        "n_surfaced_total",
        "n_surfaced_ungrounded",
        "support_rate_mean_surfaced",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def plot_figure(rows: list[dict], conservative: dict, selected: dict | None, path: Path) -> None:
    taus = [r["tau"] for r in rows]
    ar = [r["answer_rate"] for r in rows]
    aa = [r["abstention_accuracy"] for r in rows]
    ur = [r["ungrounded_rate_response"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(taus, ar, label="Answer Rate (answerable, n=36)", color="#1f77b4")
    ax.plot(taus, aa, label="Abstention Accuracy (unanswerable, n=17)", color="#2ca02c")
    ax.plot(
        taus, ur,
        label="Response-level Ungrounded Rate (over surfaced)",
        color="#d62728", alpha=0.55, linestyle="--",
    )
    ax.axhline(ABSTENTION_ACCURACY_MIN, color="#2ca02c", alpha=0.2, linewidth=0.8)
    ax.axhline(UNGROUNDED_RATE_MAX, color="#d62728", alpha=0.2, linewidth=0.8)

    ax.plot(
        conservative["tau"], conservative["answer_rate"],
        marker="o", color="#1f77b4", markersize=9, markeredgecolor="black",
        linestyle="none", label=f"Shipped τ = {conservative['tau']:.2f}",
    )
    if selected is not None and selected["tau"] != conservative["tau"]:
        ax.plot(
            selected["tau"], selected["answer_rate"],
            marker="D", color="#ff7f0e", markersize=9, markeredgecolor="black",
            linestyle="none", label=f"Retuned τ = {selected['tau']:.2f}",
        )

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Support-rate threshold τ")
    ax.set_ylabel("Rate")
    ax.set_title(
        "BM25-fallback support-rate retuning: operating points under safety constraints"
    )
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> int:
    here = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path,
                        default=here / "results/runs/b3_generative_bm25_fallback_final")
    parser.add_argument("--golden-set", type=Path,
                        default=here / "eval/golden_set/golden_set.csv")
    parser.add_argument("--out-csv", type=Path,
                        default=here / "results/tables/bm25_threshold_retuning.csv")
    parser.add_argument("--out-summary", type=Path,
                        default=here / "results/tables/bm25_threshold_retuning_summary.json")
    parser.add_argument("--out-fig", type=Path,
                        default=here / "docs/report/figures/fig_bm25_retuned_operating_point.png")
    parser.add_argument("--step", type=float, default=0.01)
    parser.add_argument("--scope", choices=("all", "test", "dev"), default="all")
    args = parser.parse_args()

    jsonl = args.run_dir / "outputs.jsonl"
    summary_path = args.run_dir / "summary.json"
    if not jsonl.exists():
        print(f"ERROR: missing {jsonl}", file=sys.stderr)
        return 2
    if not summary_path.exists():
        print(f"ERROR: missing {summary_path}", file=sys.stderr)
        return 2
    if not args.golden_set.exists():
        print(f"ERROR: missing {args.golden_set}", file=sys.stderr)
        return 2

    records = load_records(jsonl)
    summary = json.loads(summary_path.read_text())
    golden = load_golden(args.golden_set)

    problems = check_required_fields(records)
    if problems:
        for p in problems:
            print(f"FIELD-ISSUE: {p}", file=sys.stderr)
        print("ERROR: required fields missing; aborting before writing artefacts",
              file=sys.stderr)
        return 3

    # Scope filtering. The headline B3-Generative result in summary.json
    # is over all 63 records, so we default to scope='all'.
    if args.scope != "all":
        records = [
            r for r in records
            if golden.get(r["query_id"], {}).get("split", "") == args.scope
        ]
        if not records:
            print(f"ERROR: no records in scope='{args.scope}'", file=sys.stderr)
            return 3

    # Denominator reconciliation (gate G2). Only applied when scope='all'.
    cats = [r["category"] for r in records]
    n_answ = sum(c == "answerable" for c in cats)
    n_unansw = sum(c == "unanswerable" for c in cats)
    n_contra = sum(c == "contradiction" for c in cats)
    if args.scope == "all":
        if (len(records), n_answ, n_unansw, n_contra) != (63, 36, 17, 10):
            print(
                f"ERROR (G2): denominators (total={len(records)}, "
                f"answerable={n_answ}, unanswerable={n_unansw}, "
                f"contradiction={n_contra}) do not match the expected "
                f"(63, 36, 17, 10).",
                file=sys.stderr,
            )
            return 3

    taus = thresholds(args.step)
    rows = [metrics_at(records, t) for t in taus]

    # Gate G1: conservative point must reproduce summary.json.
    conservative = next((r for r in rows if r["tau"] == SHIPPED_TAU), None)
    if conservative is None:
        print("ERROR (G1): conservative tau=0.80 row not produced", file=sys.stderr)
        return 3
    ok, issues = validate_against_summary(conservative, summary)
    if not ok and args.scope == "all":
        print("ERROR (G1): conservative point does not match summary.json:",
              file=sys.stderr)
        for it in issues:
            print(f"  - {it}", file=sys.stderr)
        return 3

    selected, interpretation = select_operating_point(rows)

    # Quantify coverage uplift vs the conservative shipped point, and detect
    # the case where the selection rule technically finds a feasible point
    # but it sits on the same Answer-Rate plateau as tau=0.80 (i.e. no
    # genuine coverage rescue). This keeps the report wording honest.
    coverage_uplift_pp = 0.0
    if selected is not None:
        coverage_uplift_pp = round(
            100.0 * (selected["answer_rate"] - conservative["answer_rate"]), 2
        )
    if (
        selected is not None
        and interpretation == "balanced_point_meets_constraints"
        and abs(coverage_uplift_pp) < 0.5  # within half a percentage point
    ):
        interpretation = "feasible_region_matches_conservative_plateau"

    # Write CSV.
    write_csv(rows, args.out_csv)

    # Build and write summary JSON.
    summary_out = {
        "scope": args.scope,
        "n_total": len(records),
        "n_answerable": n_answ,
        "n_unanswerable": n_unansw,
        "n_contradiction": n_contra,
        "conservative_threshold": SHIPPED_TAU,
        "conservative_answer_rate": conservative["answer_rate"],
        "conservative_abstention_accuracy": conservative["abstention_accuracy"],
        "conservative_ungrounded_rate_response": conservative["ungrounded_rate_response"],
        "conservative_n_answered": conservative["n_answered"],
        "conservative_n_abstained": conservative["n_abstained"],
        "selected_threshold": selected["tau"] if selected else None,
        "selected_answer_rate": selected["answer_rate"] if selected else None,
        "selected_abstention_accuracy": (
            selected["abstention_accuracy"] if selected else None
        ),
        "selected_ungrounded_rate_response": (
            selected["ungrounded_rate_response"] if selected else None
        ),
        "selected_n_answered": selected["n_answered"] if selected else None,
        "selected_n_abstained": selected["n_abstained"] if selected else None,
        "selection_rule": (
            "argmax answer_rate s.t. abstention_accuracy>=0.80 and "
            "ungrounded_rate_response<=0.05 and n_answered>=1; "
            "tie-break: higher abstention_accuracy, lower ungrounded_rate, higher tau"
        ),
        "constraints_met": interpretation in (
            "balanced_point_meets_constraints",
            "feasible_region_matches_conservative_plateau",
        ),
        "interpretation": interpretation,
        "coverage_uplift_pp": coverage_uplift_pp,
        "reconstructed_conservative_matches_summary_json": ok,
        "source_run": str(args.run_dir.relative_to(here)) if args.run_dir.is_absolute()
                       and args.run_dir.is_relative_to(here) else str(args.run_dir),
        "generated_by": "scripts/analyse_bm25_threshold_retuning.py",
        "no_llm_calls": True,
        "sweep_step": args.step,
    }
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.write_text(json.dumps(summary_out, indent=2) + "\n")

    # Plot figure.
    plot_figure(rows, conservative, selected, args.out_fig)

    # Console report.
    print(f"Loaded {len(records)} records (scope={args.scope}).")
    print(
        f"Denominators: total={len(records)} answerable={n_answ} "
        f"unanswerable={n_unansw} contradiction={n_contra}"
    )
    print("Gate G1 (conservative point reconstruction):")
    print(
        f"  reconstructed tau=0.80 -> answer_rate={conservative['answer_rate']:.4f} "
        f"(summary.json={summary.get('answer_rate')}), "
        f"abstention_accuracy={conservative['abstention_accuracy']:.4f} "
        f"(summary.json={summary.get('abstention_accuracy')}), "
        f"ungrounded_rate_response={conservative['ungrounded_rate_response']:.4f} "
        f"(summary.json={summary.get('ungrounded_rate')})"
    )
    print(f"  G1 PASS={ok}")
    if selected is not None:
        print(
            f"Selected retuned point: tau={selected['tau']:.2f}, "
            f"answer_rate={selected['answer_rate']:.4f}, "
            f"abstention_accuracy={selected['abstention_accuracy']:.4f}, "
            f"ungrounded_rate_response={selected['ungrounded_rate_response']:.4f}, "
            f"n_answered={selected['n_answered']}, n_abstained={selected['n_abstained']}"
        )
    else:
        print("Selected retuned point: NONE (no safe candidate)")
    print(f"Interpretation: {interpretation}")
    print(f"Wrote CSV     : {args.out_csv}")
    print(f"Wrote summary : {args.out_summary}")
    print(f"Wrote figure  : {args.out_fig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
