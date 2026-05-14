"""Phase N + Phase 9 tests: the final consistency-check script must pass on
the real report, and must catch fixture-injected violations.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/final_consistency_check.py"


def test_final_consistency_check_exits_clean():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True
    )
    assert proc.returncode == 0, (
        f"final_consistency_check failed:\n{proc.stdout}\n{proc.stderr}"
    )
    assert "no issues found" in proc.stdout


def _import_consistency_module():
    """Import the consistency-check script as a module for direct function testing."""
    spec = importlib.util.spec_from_file_location("_fcc", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


def test_banned_substring_detected_in_fixture():
    """Inject a banned phrase into a fixture string and verify the check fires."""
    mod = _import_consistency_module()
    fake_report = "Some prose. design-time estimates from Sprint 5. More prose."
    issues = mod.check_banned_substrings(fake_report)
    assert any("design-time" in i for i in issues)


def test_fr_cross_reference_mistake_detected_in_fixture():
    """Phase 9 negative check: 'Abstention Accuracy ... (Objective 4 / FR3)' is wrong."""
    mod = _import_consistency_module()
    fake = "We meet Abstention Accuracy ≥ 80% (Objective 4 / FR3) on the unanswerable set."
    issues = mod.check_fr_cross_references(fake)
    assert any("FR3" in i for i in issues)


def test_b4_backend_claim_negative_fixture():
    """Phase 9: a fake report claiming 'B4 on the hybrid backend' triggers the check."""
    mod = _import_consistency_module()
    fake = (
        "The B4 Conservative Hybrid Mode runs on the hybrid backend with dense and BM25 "
        "fused via RRF."
    )
    issues = mod.check_b4_backend_claim(fake)
    # The real B4 run_config says backend_used=bm25, so this fake should be flagged.
    assert any("backend_used" in i for i in issues), issues


def test_adversarial_completion_negative_fixture():
    """Phase 9: a fake report saying generative adversarial completed when summary
    says n/a should trigger the check."""
    mod = _import_consistency_module()
    fake = "Note: the generative adversarial arm completed with safe rate 100%."
    issues = mod.check_adversarial_completion(fake)
    # We expect the check to fire because the current adversarial_summary.csv
    # has all n/a in the generative rows.
    assert any("generative" in i for i in issues), issues
