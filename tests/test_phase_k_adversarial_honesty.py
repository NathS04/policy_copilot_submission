"""Phase K honesty tests.

The user did not supply an OPENAI_API_KEY in this session, so the
generative adversarial arm could not be re-run. The existing summary
preserves the original 'n/a' values from the prior insufficient_quota
error. These tests protect against ever silently replacing 'n/a' with
'safe' without a real successful run.

Also asserts that the extractive arm continues to report a real safe
rate (not n/a).
"""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADVERSARIAL = ROOT / "eval/adversarial/adversarial_summary.csv"


def _rows():
    with ADVERSARIAL.open() as f:
        return list(csv.DictReader(f))


def test_extractive_arm_has_real_rates():
    """Extractive arm must report numeric safe rates (not n/a)."""
    rows = [r for r in _rows() if r["mode"] == "extractive"]
    assert rows
    for r in rows:
        assert r["safe_response_rate"] != "n/a", (
            f"extractive {r['attack_type']}: safe_response_rate should be numeric"
        )
        # parseable
        float(r["safe_response_rate"])


def test_generative_arm_honesty():
    """Generative arm rows must EITHER all be n/a (no live run) OR all
    be numeric (live run completed). Never a mix."""
    rows = [r for r in _rows() if r["mode"] == "generative"]
    assert rows
    is_na = [r["safe_response_rate"] == "n/a" for r in rows]
    # All same: either every generative row is n/a or none is.
    assert all(is_na) or not any(is_na), (
        "generative adversarial rows are inconsistent: mix of n/a and numeric. "
        "This violates the 'no fake success on API error' rule."
    )


def test_api_error_count_consistent_with_safe_rate():
    """If n_api_error == n, safe_response_rate must be n/a."""
    bad = []
    for r in _rows():
        n = int(r["n"])
        n_api = int(r["n_api_error"])
        rate = r["safe_response_rate"]
        if n_api == n and rate != "n/a":
            bad.append((r["attack_type"], r["mode"], n, n_api, rate))
    assert not bad, f"rows with full API error but non-n/a rate: {bad}"
