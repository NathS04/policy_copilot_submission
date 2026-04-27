"""Compute per-axis statistics and inter-rater agreement for the
per-query independent reviewer evaluation (Round 2).

Reads:  eval/human_eval/per_query_raw.csv (long form)
        OR eval/human_eval/per_query_raw.csv in wide form (Google
        Forms default); the script reshapes wide-form input
        automatically.

Writes:
  docs/evidence/human_eval/anonymised_scores.csv (per-query rows)
  docs/evidence/human_eval/summary_stats.csv     (means, SDs, alphas)
  docs/evidence/human_eval/inter_rater_agreement.md (narrative)

If the input CSV is missing or has fewer than 3 reviewers, the script
writes an honest "not yet collected" / "agreement not computable"
report rather than fabricating numbers.

Usage:
  python scripts/compute_human_eval.py
  python scripts/compute_human_eval.py --raw eval/human_eval/per_query_raw.csv

Krippendorff's alpha is computed from scratch (no third-party
dependency) using the ordinal-distance metric appropriate for
1-5 Likert ratings.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
RAW_DEFAULT = ROOT / "eval" / "human_eval" / "per_query_raw.csv"
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "human_eval"
# Round 2 (per-query) outputs are namespaced so they never collide with
# the Round 1 aggregate files (anonymised_scores.csv, summary_stats.csv).
ANON_OUT = EVIDENCE_DIR / "per_query_anonymised_scores.csv"
SUMMARY_OUT = EVIDENCE_DIR / "per_query_summary_stats.csv"
AGREEMENT_OUT = EVIDENCE_DIR / "inter_rater_agreement.md"

AXES = ["correctness", "groundedness", "citation_usefulness",
        "usefulness", "trust_calibration"]
LIKERT_VALUES = [1, 2, 3, 4, 5]


def _load_long_csv(path: Path) -> list[dict]:
    """Load the long-form per-query CSV. Returns [] if file missing."""
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    cleaned: list[dict] = []
    for r in rows:
        if not r.get("participant_id") or not r.get("query_id"):
            continue
        try:
            for axis in AXES:
                r[axis] = int(r[axis])
        except (ValueError, TypeError, KeyError):
            continue
        cleaned.append(r)
    return cleaned


def _try_reshape_wide(path: Path) -> list[dict]:
    """Best-effort reshape of Google-Forms-style wide CSV into long
    form. Looks for columns named like Q01_correctness, Q01_groundedness,
    etc., and emits one long row per (participant, query)."""
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return []
    long_rows: list[dict] = []
    for r in rows:
        pid = r.get("participant_id") or r.get("Q0_id") or r.get("Anonymous Tag")
        role = r.get("role") or r.get("Q1_role") or r.get("Role")
        if not pid:
            continue
        for q in [f"Q{str(i).zfill(2)}" for i in range(1, 21)]:
            scores = {}
            for axis in AXES:
                key_candidates = [
                    f"{q}_{axis}",
                    f"{q}_{axis.replace('_', '')}",
                    f"{q} {axis}",
                ]
                val = None
                for kc in key_candidates:
                    if kc in r and r[kc] not in ("", None):
                        try:
                            val = int(r[kc])
                            break
                        except (ValueError, TypeError):
                            pass
                if val is None:
                    break
                scores[axis] = val
            if len(scores) != len(AXES):
                continue
            long_rows.append({
                "participant_id": pid,
                "role": role or "",
                "query_id": q,
                "query_type": "",
                "mode": "B3-Gen",
                **scores,
                "short_comment": r.get(f"{q}_comment", ""),
            })
    return long_rows


def _summary(values: list[int]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "stdev": None, "median": None,
                "min": None, "max": None}
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 3),
        "stdev": round(statistics.pstdev(values), 3) if len(values) > 1 else 0.0,
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
    }


def _krippendorff_alpha_ordinal(matrix: dict[str, dict[str, int]]) -> float | None:
    """Compute Krippendorff's alpha with ordinal distance metric.

    matrix[item_id][rater_id] = rating (int).

    Returns None if there are fewer than 2 raters or fewer than 2
    distinct values across all ratings.
    """
    item_ids = [iid for iid, rs in matrix.items() if len(rs) >= 2]
    if len(item_ids) < 2:
        return None

    all_ratings = [v for iid in item_ids for v in matrix[iid].values()]
    if len(set(all_ratings)) < 2:
        return None

    value_counts = defaultdict(int)
    for v in all_ratings:
        value_counts[v] += 1
    sorted_values = sorted(value_counts)
    n_total = sum(value_counts.values())

    def ordinal_distance(c: int, k: int) -> float:
        if c == k:
            return 0.0
        lo, hi = (c, k) if c < k else (k, c)
        running = 0.0
        for v in sorted_values:
            if lo < v < hi:
                running += value_counts[v]
        running += (value_counts[c] + value_counts[k]) / 2.0
        return running ** 2

    observed_disagreement = 0.0
    item_terms = 0.0
    for iid in item_ids:
        ratings = list(matrix[iid].values())
        m = len(ratings)
        if m < 2:
            continue
        item_terms += m
        pair_sum = 0.0
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                pair_sum += ordinal_distance(ratings[i], ratings[j])
        observed_disagreement += pair_sum / (m - 1)

    if item_terms == 0:
        return None
    observed_disagreement = observed_disagreement / item_terms

    expected_disagreement = 0.0
    sorted_vals_list = sorted_values
    for c in sorted_vals_list:
        for k in sorted_vals_list:
            if c == k:
                continue
            expected_disagreement += value_counts[c] * value_counts[k] * ordinal_distance(c, k)
    if n_total <= 1:
        return None
    expected_disagreement = expected_disagreement / (n_total * (n_total - 1))

    if expected_disagreement == 0:
        return None
    return 1.0 - (observed_disagreement / expected_disagreement)


def _bootstrap_ci(matrix: dict[str, dict[str, int]], n_iter: int = 1000,
                  seed: int = 42) -> tuple[float | None, float | None]:
    """Resample items with replacement to estimate a 95% CI for alpha."""
    item_ids = [iid for iid, rs in matrix.items() if len(rs) >= 2]
    if len(item_ids) < 4:
        return None, None
    rng = random.Random(seed)
    alphas: list[float] = []
    for _ in range(n_iter):
        sample_ids = [rng.choice(item_ids) for _ in item_ids]
        sample_matrix = {f"{iid}#{i}": dict(matrix[iid]) for i, iid in enumerate(sample_ids)}
        a = _krippendorff_alpha_ordinal(sample_matrix)
        if a is not None:
            alphas.append(a)
    if len(alphas) < 50:
        return None, None
    alphas.sort()
    lo = alphas[int(0.025 * len(alphas))]
    hi = alphas[int(0.975 * len(alphas)) - 1]
    return round(lo, 3), round(hi, 3)


def _bin_likert(v: int) -> str:
    if v <= 2:
        return "low"
    if v == 3:
        return "mid"
    return "high"


def _pairwise_agreement(matrix: dict[str, dict[str, int]]) -> float | None:
    pair_total = 0
    pair_agree = 0
    for ratings in matrix.values():
        bins = [_bin_likert(v) for v in ratings.values()]
        m = len(bins)
        if m < 2:
            continue
        for i in range(m):
            for j in range(i + 1, m):
                pair_total += 1
                if bins[i] == bins[j]:
                    pair_agree += 1
    if pair_total == 0:
        return None
    return round(pair_agree / pair_total, 3)


def _write_anonymised(rows: list[dict]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["participant_id", "role", "query_id", "query_type", "mode",
              "correctness", "groundedness", "citation_usefulness",
              "usefulness", "trust_calibration", "short_comment"]
    with ANON_OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _write_summary(rows: list[dict], alphas: dict[str, float | None],
                   alpha_cis: dict[str, tuple[float | None, float | None]],
                   pairwise: dict[str, float | None]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["axis", "scope", "n", "mean", "stdev", "median", "min", "max",
              "krippendorff_alpha", "alpha_ci_lo", "alpha_ci_hi",
              "pairwise_pct_agreement_binned"]
    out_rows: list[dict] = []
    for axis in AXES:
        scopes: dict[str, list[int]] = defaultdict(list)
        for r in rows:
            scopes["overall"].append(r[axis])
            qt = (r.get("query_type") or "").strip().lower() or "unknown"
            scopes[qt].append(r[axis])
        for scope, vals in scopes.items():
            s = _summary(vals)
            row = {"axis": axis, "scope": scope, **s,
                   "krippendorff_alpha": "", "alpha_ci_lo": "",
                   "alpha_ci_hi": "", "pairwise_pct_agreement_binned": ""}
            if scope == "overall":
                a = alphas.get(axis)
                lo, hi = alpha_cis.get(axis, (None, None))
                p = pairwise.get(axis)
                row["krippendorff_alpha"] = "" if a is None else round(a, 3)
                row["alpha_ci_lo"] = "" if lo is None else lo
                row["alpha_ci_hi"] = "" if hi is None else hi
                row["pairwise_pct_agreement_binned"] = "" if p is None else p
            out_rows.append(row)
    with SUMMARY_OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)


def _write_agreement(rows: list[dict], n_raters: int,
                     alphas: dict[str, float | None],
                     alpha_cis: dict[str, tuple[float | None, float | None]],
                     pairwise: dict[str, float | None],
                     reason: str | None = None) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    if reason:
        body = [
            "# Inter-rater Agreement",
            "",
            "**Status:** *Not computable from currently available data.*",
            "",
            f"**Reason:** {reason}",
            "",
            "## What this means",
            "",
            "The Round 1 evaluation (P1-P6, April 2026) recorded only",
            "per-participant aggregate Likert scores. Agreement metrics",
            "such as Krippendorff's alpha or Fleiss' kappa require",
            "per-(participant, query) ratings. The form spec at",
            "`eval/human_eval/forms/per_query_form_spec.md` collects",
            "exactly that schema; once at least 3 reviewers complete",
            "the form, this file will be regenerated automatically by",
            "`python scripts/compute_human_eval.py`.",
            "",
            "## Why we don't fabricate it",
            "",
            "Reporting a fabricated alpha (or an alpha computed from",
            "aggregate data, which is mathematically meaningless)",
            "would be academically dishonest. The dissertation surfaces",
            "this as Limitation L5 (`Limited Independent Human",
            "Evaluation`) in Section 5.2 and in Appendix B.10.",
            "",
        ]
        AGREEMENT_OUT.write_text("\n".join(body))
        return

    n_items = len({r["query_id"] for r in rows})
    body = [
        "# Inter-rater Agreement",
        "",
        f"**Status:** Computed from {n_raters} reviewers x {n_items} queries x {len(AXES)} axes.",
        "",
        "## Method",
        "",
        "Inter-rater agreement is reported as **Krippendorff's alpha**",
        "with the ordinal-distance metric appropriate for 1-5 Likert",
        "ratings (Krippendorff, 2004). Bootstrap 95% confidence intervals",
        "are obtained by resampling items with replacement (1,000",
        "iterations, seed = 42). As a non-parametric robustness check we",
        "also report binned pairwise % agreement after the mapping",
        "{1-2 -> low, 3 -> mid, 4-5 -> high}.",
        "",
        "All metrics are computed by `scripts/compute_human_eval.py`,",
        "which is committed alongside the data and tested against the",
        "Krippendorff (2004) example dataset (see `tests/`).",
        "",
        "## Results",
        "",
        "| Axis | Krippendorff alpha | 95% CI | Pairwise % (binned) |",
        "| :--- | :---: | :---: | :---: |",
    ]
    for axis in AXES:
        a = alphas.get(axis)
        lo, hi = alpha_cis.get(axis, (None, None))
        p = pairwise.get(axis)
        a_str = "n/a" if a is None else f"{a:.3f}"
        ci_str = "n/a" if lo is None or hi is None else f"[{lo:.3f}, {hi:.3f}]"
        p_str = "n/a" if p is None else f"{int(p * 100)}%"
        body.append(f"| {axis.replace('_', ' ').title()} | {a_str} | {ci_str} | {p_str} |")

    body += [
        "",
        "## Interpretation",
        "",
        "Krippendorff (2004) suggests informal cut-offs of alpha >= 0.80",
        "for confident interpretation, alpha >= 0.667 for tentative",
        "interpretation, and alpha < 0.667 as evidence that the",
        "underlying rating task is too noisy for strong claims. The",
        "values above are reported honestly without normative",
        "framing; the dissertation (Section 4.10 and Appendix B.10)",
        "discusses what the observed alpha implies for the",
        "trustworthiness of the per-axis means.",
        "",
        "## Limitations",
        "",
        f"- Sample is small (n = {n_raters} reviewers).",
        "- Reviewers are technically literate CS peers, not domain",
        "  specialists in compliance or policy.",
        "- The author is identifiable as the recruiter, so the",
        "  evaluation is author-facilitated rather than fully",
        "  blinded.",
        "- Per-query results are reported in the report (Appendix",
        "  B.10) and the raw per-query rows are in",
        "  `docs/evidence/human_eval/anonymised_scores.csv`.",
        "",
    ]
    AGREEMENT_OUT.write_text("\n".join(body))


def _short(path: Path) -> str:
    """Best-effort relative-to-ROOT display path."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", default=str(RAW_DEFAULT),
                        help="Path to per_query_raw.csv (long or wide form)")
    args = parser.parse_args()
    raw_path = Path(args.raw)

    rows = _load_long_csv(raw_path)
    if not rows:
        rows = _try_reshape_wide(raw_path)

    if not rows:
        reason = (f"`{_short(raw_path)}` is missing or empty. "
                  "Distribute the form at "
                  "`eval/human_eval/forms/per_query_form_spec.md` and "
                  "save the CSV export there.")
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        if not ANON_OUT.exists():
            with ANON_OUT.open("w", newline="") as fh:
                fh.write("participant_id,role,query_id,query_type,mode,"
                         "correctness,groundedness,citation_usefulness,"
                         "usefulness,trust_calibration,short_comment\n")
        # Note: Round 1 aggregate files (anonymised_scores.csv,
        # summary_stats.csv) are intentionally left untouched here.
        # Only the Round-2-namespaced files are written.
        _write_agreement([], 0,
                         {a: None for a in AXES},
                         {a: (None, None) for a in AXES},
                         {a: None for a in AXES},
                         reason=reason)
        print(f"  no per-query data at {raw_path}; wrote 'not yet collected' agreement report.")
        return 0

    n_raters = len({r["participant_id"] for r in rows})
    print(f"  loaded {len(rows)} rows, {n_raters} reviewers, "
          f"{len({r['query_id'] for r in rows})} queries.")

    alphas: dict[str, float | None] = {}
    alpha_cis: dict[str, tuple[float | None, float | None]] = {}
    pairwise: dict[str, float | None] = {}
    if n_raters >= 3:
        for axis in AXES:
            matrix: dict[str, dict[str, int]] = defaultdict(dict)
            for r in rows:
                matrix[r["query_id"]][r["participant_id"]] = int(r[axis])
            alphas[axis] = _krippendorff_alpha_ordinal(matrix)
            alpha_cis[axis] = _bootstrap_ci(matrix)
            pairwise[axis] = _pairwise_agreement(matrix)
    else:
        for axis in AXES:
            alphas[axis] = None
            alpha_cis[axis] = (None, None)
            pairwise[axis] = None

    _write_anonymised(rows)
    _write_summary(rows, alphas, alpha_cis, pairwise)

    if n_raters < 3:
        reason = (f"only {n_raters} reviewer(s) submitted; "
                  "Krippendorff's alpha is undefined for fewer than "
                  "two raters and statistically uninformative for "
                  "fewer than three.")
        _write_agreement(rows, n_raters, alphas, alpha_cis, pairwise, reason=reason)
    else:
        _write_agreement(rows, n_raters, alphas, alpha_cis, pairwise)

    print(f"  wrote {_short(ANON_OUT)}")
    print(f"  wrote {_short(SUMMARY_OUT)}")
    print(f"  wrote {_short(AGREEMENT_OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
