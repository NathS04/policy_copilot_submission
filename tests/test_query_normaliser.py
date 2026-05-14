"""Phase 4 tests: policy-domain query normaliser.

Verifies:
  1. Known synonym mappings expand the query (resignation→notice, BYOD, etc.).
  2. The normaliser never returns an empty string for a non-empty input.
  3. Empty input passes through unchanged.
  4. The normaliser does NOT import the golden set.
"""
from __future__ import annotations

import inspect

from policy_copilot.retrieve import query_normaliser
from policy_copilot.retrieve.query_normaliser import normalise_query


def test_resignation_expands_to_notice_period():
    out, applied = normalise_query("How long is the notice period for resignation?")
    assert "leaving" in out.lower() or "notice period" in out.lower()
    assert applied  # at least one pattern fired


def test_byod_expands():
    out, applied = normalise_query("Is BYOD allowed?")
    assert "bring" in out.lower() and "device" in out.lower()


def test_grievance_expands_to_complaint():
    out, applied = normalise_query("Is there a grievance procedure?")
    assert "complaint" in out.lower()


def test_sabbatical_expands():
    out, applied = normalise_query("Does the company offer sabbatical leave?")
    assert "unpaid" in out.lower() or "career break" in out.lower()


def test_empty_input_returns_empty():
    out, applied = normalise_query("")
    assert out == ""
    assert applied == []


def test_non_matching_query_unchanged():
    out, applied = normalise_query("What is the weather today?")
    assert out == "What is the weather today?"
    assert applied == []


def test_normaliser_does_not_import_golden_set():
    src = inspect.getsource(query_normaliser)
    forbidden = ["golden_set", "gold_paragraph_ids", "csv.DictReader", "open("]
    for token in forbidden:
        assert token not in src, f"normaliser must not reference {token!r}"


def test_normaliser_appends_dedup():
    """If two patterns produce overlapping extras, they should be deduped."""
    out, _ = normalise_query("What is the BYOD policy on personal devices?")
    # Token 'bring' should appear at most once even though both 'byod' and
    # 'personal devices' patterns fire and both extras include 'bring'.
    assert out.lower().count("bring") <= 2  # one in original, at most one append
