"""Phase 4 test: nothing in src/policy_copilot/retrieve/ reads the golden set.

This is an integrity guard: retrieval code must NEVER use gold paragraph
IDs at inference time. Violating this would invalidate every recall
metric in the project. The test walks each .py file under the retrieve
package and asserts that none of them imports or references the golden
set CSV path or any gold_paragraph_ids field.
"""
from __future__ import annotations

from pathlib import Path


RETRIEVE_DIR = Path(__file__).resolve().parents[1] / "src/policy_copilot/retrieve"


FORBIDDEN_TOKENS = [
    "golden_set",
    "golden_set.csv",
    "golden_set_v2_corrected",
    "gold_paragraph_ids",
    "gold_doc_ids",
    'category == "answerable"',
    'category == "unanswerable"',
]


def test_no_golden_set_references_in_retrieve_package():
    bad = []
    for py in RETRIEVE_DIR.rglob("*.py"):
        text = py.read_text()
        for tok in FORBIDDEN_TOKENS:
            if tok in text:
                bad.append((py.name, tok))
    assert not bad, f"golden-label leakage in retrieve package: {bad}"
