"""Phase L tests: new artefacts are registered and on disk."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run_summary_v2_exists_and_has_b4_row():
    p = ROOT / "results/tables/run_summary_v2.csv"
    assert p.exists()
    with p.open() as f:
        rows = list(csv.DictReader(f))
    labels = [r.get("label") for r in rows]
    assert "B4 Conservative Hybrid" in labels


def test_fig_baselines_v2_exists():
    p = ROOT / "docs/report/figures/fig_baselines_v2.png"
    assert p.exists()
    assert p.stat().st_size > 5_000  # non-empty png


def test_manifest_lists_new_tables():
    p = ROOT / "results/manifest.json"
    assert p.exists()
    m = json.loads(p.read_text())
    tables = set(m.get("tables", []))
    # at minimum the v2 aggregator and the bootstrap-CI v2 must be present
    for name in (
        "run_summary_v2.csv",
        "statistical_confidence_v2.csv",
        "golden_set_label_audit.csv",
        "component_ablation_final.csv",
        "contradiction_evaluation_v2.csv",
    ):
        assert name in tables, f"manifest missing {name}; got {sorted(tables)}"
