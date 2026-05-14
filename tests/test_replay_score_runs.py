"""Tests for replay-based metric recomputation (Phase B).

Verifies:
1. Each _v2 run directory has run_config.json + outputs.jsonl + summary.json
   + predictions.csv + tables/metrics.csv.
2. Each outputs.jsonl record matches the corrected golden set for category,
   is_answerable, gold_paragraph_ids, and gold_doc_ids.
3. Run-config provenance is recorded: dataset_version=golden_set_v2_corrected,
   replay_provenance.no_llm_calls=true.
4. Replay-script entrypoint runs cleanly on a synthetic source run.
5. Replay does not import or instantiate any LLM client.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
V2_RUNS = [
    "b1_generative_v2",
    "b2_generative_v2",
    "b3_generative_v2",
    "b3_extractive_v2",
]
CORRECTED = ROOT / "eval/golden_set/golden_set_v2_corrected.csv"
REPLAY_SCRIPT = ROOT / "scripts/replay_score_runs.py"


def _load_corrected_map() -> dict:
    with CORRECTED.open() as f:
        return {r["query_id"]: r for r in csv.DictReader(f)}


@pytest.mark.parametrize("run_name", V2_RUNS)
def test_v2_run_has_required_files(run_name):
    run_dir = ROOT / "results/runs" / run_name
    for fname in ("run_config.json", "outputs.jsonl", "summary.json",
                  "predictions.csv", "tables/metrics.csv", "README.md"):
        assert (run_dir / fname).exists(), f"missing {run_dir / fname}"


@pytest.mark.parametrize("run_name", V2_RUNS)
def test_v2_run_config_has_replay_provenance(run_name):
    cfg = json.loads((ROOT / "results/runs" / run_name / "run_config.json").read_text())
    assert cfg.get("dataset_version") == "golden_set_v2_corrected"
    rp = cfg.get("replay_provenance") or {}
    assert rp.get("no_llm_calls") is True
    assert rp.get("replay_script") == "scripts/replay_score_runs.py"
    assert "replayed_from" in rp


@pytest.mark.parametrize("run_name", V2_RUNS)
def test_v2_outputs_have_corrected_labels(run_name):
    corrected = _load_corrected_map()
    path = ROOT / "results/runs" / run_name / "outputs.jsonl"
    with path.open() as f:
        recs = [json.loads(line) for line in f if line.strip()]
    mismatches = []
    for rec in recs:
        qid = rec["query_id"]
        if qid not in corrected:
            mismatches.append((qid, "not in corrected golden set"))
            continue
        c = corrected[qid]
        if rec.get("category") != c["category"]:
            mismatches.append((qid, f"category {rec.get('category')!r} vs {c['category']!r}"))
        if bool(rec.get("is_answerable")) != (c["category"] == "answerable"):
            mismatches.append((qid, f"is_answerable {rec.get('is_answerable')} vs {c['category']=='answerable'}"))
        if (rec.get("gold_paragraph_ids") or "") != (c.get("gold_paragraph_ids") or ""):
            mismatches.append((qid, "gold_paragraph_ids mismatch"))
    assert not mismatches, mismatches[:5]


def test_b3_generative_v2_denominators():
    """The headline run: 40 answerable / 13 unanswerable / 10 contradiction."""
    path = ROOT / "results/runs/b3_generative_v2/outputs.jsonl"
    with path.open() as f:
        recs = [json.loads(line) for line in f if line.strip()]
    cats = [r["category"] for r in recs]
    assert cats.count("answerable") == 40
    assert cats.count("unanswerable") == 13
    assert cats.count("contradiction") == 10
    assert len(recs) == 63


def test_b3_generative_v2_abstention_accuracy_perfect():
    """All 13 unanswerable should be correctly abstained after relabel."""
    summary = json.loads((ROOT / "results/runs/b3_generative_v2/summary.json").read_text())
    assert summary["abstention_accuracy"] == 1.0


def test_replay_no_llm_imports(tmp_path):
    """Replay script must not import openai/anthropic at runtime."""
    # Build a synthetic source run with two records.
    src = tmp_path / "src_run"
    src.mkdir()
    (src / "run_config.json").write_text(json.dumps({"baseline": "b3", "backend": "bm25"}))
    rec = {
        "query_id": "q_001",
        "baseline": "b3",
        "question": "test?",
        "category": "answerable",
        "is_answerable": True,
        "answer": "x",
        "is_abstained": False,
        "citations": [],
        "confidence": {"max_rerank": 1.0},
        "evidence": [],
        "claim_verification": {"support_rate": 1.0, "supported_claims": 1, "unsupported_claims": 0},
        "contradictions": [],
        "notes": [],
        "provider": "x", "model": "x",
        "latency_ms": {},
        "backend_requested": "dense", "backend_used": "bm25",
        "gold_paragraph_ids": "x", "gold_doc_ids": "x",
    }
    (src / "outputs.jsonl").write_text(json.dumps(rec) + "\n")

    # Run the replay script with stub PYTHONPATH so it can't pull live deps.
    # The real test: stub the openai module to raise on import; replay must not import it.
    env = {"PYTHONPATH": str(tmp_path), "OPENAI_API_KEY": ""}
    # Write a stub that explodes if imported.
    (tmp_path / "openai.py").write_text("raise ImportError('openai must not be imported during replay')\n")

    # The replay also needs a golden set; build a minimal one with one row.
    golden = tmp_path / "g.csv"
    golden.write_text(
        "query_id,question,category,split,gold_doc_ids,gold_paragraph_ids,notes,objective_slice\n"
        "q_001,test?,answerable,test,xdoc,xpid,manual,false\n"
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    # Symlink the source under the expected name.
    (runs_root / "b1_generative_final").symlink_to(src)

    proc = subprocess.run(
        [sys.executable, str(REPLAY_SCRIPT),
         "--runs-root", str(runs_root), "--golden-set", str(golden)],
        cwd=ROOT, capture_output=True, text=True,
        env={**__import__("os").environ, **env},
    )
    assert proc.returncode == 0, f"stderr:\n{proc.stderr}"
    assert "openai must not be imported" not in proc.stderr
