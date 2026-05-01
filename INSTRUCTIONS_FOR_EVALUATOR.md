# Instructions for Evaluator

## Purpose

This file provides the shortest path to verify the **final reproducibility contract** for the submitted Policy Copilot package. Every step below is deterministic, runs on a consumer laptop, and does not require an LLM API key unless explicitly stated.

## Expected environment

| Requirement | Value |
| :--- | :--- |
| Python | 3.10 or newer |
| Operating system | macOS or Linux (tested) |
| Disk | ~1 GB for venv + index artefacts |
| Network | Required for `pip install` only |
| LLM API key | **Optional**; offline path requires no key |

The default reproduction path is **offline / no API key** and uses BM25 retrieval. The online / generative path is documented separately in §4 below.

## 1. Fresh install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -c "import policy_copilot; print(policy_copilot.__version__)"
```

`pip install -e ".[dev]"` installs the core dependencies plus development tools (`pytest`, `ruff`, `mypy`). It does **not** install PyTorch, FAISS, or SentenceTransformers; those live in the `[ml]` extra and are only required for dense retrieval.

The import line should print a version string (e.g. `1.0.0`). If it raises, stop and report the error.

## 2. Test suite

```bash
pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py
```

Expected on a clean install:

```text
193 passed, 1 skipped
```

The single skipped test (`test_run_eval_requires_key_in_generative`) is conditionally skipped when no API key is configured; this is intentional and documented in `tests/`.

## 3. Offline reproduction

```bash
python scripts/reproduce_offline.py
python scripts/verify_artifacts.py
```

`reproduce_offline.py` runs B2 (naive RAG) and B3 (full system) in **Extractive Mode** against the synthetic test split using the BM25 retrieval backend. No LLM calls are made; no API key is required.

`verify_artifacts.py` checks that each run directory under `results/runs/` has a complete `run_config.json + summary.json` pair, verifies that no orphan figures or tables exist in `results/figures/` and `results/tables/`, and exits 0 on success.

Expected last lines of output:

```text
All required artefacts present.
No orphan figures or tables.
```

## 4. Optional online / generative reproduction

This step requires an OpenAI or Anthropic API key and may incur cost (~15-30 LLM calls per baseline at ~$0.02 per call on `gpt-4o-mini`). Offline artefacts are already included in the submission, so the marker does **not** need to run this step to verify the dissertation's claims.

```bash
export OPENAI_API_KEY="..."        # or ANTHROPIC_API_KEY
python scripts/run_eval.py --baseline b3 --mode generative
python scripts/reproduce_online.py
```

If the API account is out of quota, the runner records `insufficient_quota` per query and writes ERROR records — the runner does **not** fabricate outputs. The Generative arm of Appendix B.12's adversarial probe was reported as `n/a` for this exact reason.

## 5. Evidence and report locations

| Path | Content |
| :--- | :--- |
| `docs/report/Final_Report_Draft.pdf` | Final dissertation, 65 pages total, 30-page body |
| `docs/evidence/README.md` | Examiner-facing evidence pack entry point |
| `docs/evidence/checklist.md` | Per-claim mapping: claim → evidence file |
| `docs/evidence/capture_guide.md` | How each artefact was produced and how to regenerate it |
| `docs/evidence/human_eval/` | Reviewer evaluation: rubric, consent text, anonymised scores, Krippendorff α |
| `docs/evidence/verification/` | Public-transfer failure taxonomy, adversarial summary, audit-export examples |
| `eval/golden_set/` | Synthetic 63-query golden set (44 test, 19 dev) and the public-transfer 20-query set |
| `eval/human_eval/` | Working copies of the human-evaluation materials |
| `eval/public_transfer/` | Failure-taxonomy CSV |
| `eval/adversarial/` | 15-query adversarial probe + extractive results |
| `data/public_transfer_corpus/` | OGL v3.0 public guidance documents + provenance.csv |
| `results/runs/` | Per-run `outputs.jsonl` and `summary.json` for every reported baseline |

## 6. Known limitations

- **Primary corpus is synthetic.** The Public Guidance Transfer Stress Test (§4.11) probes safety-property transfer to OGL public guidance, but full transfer is not demonstrated.
- **Public Guidance Transfer corpus is small** (20 queries, 8 documents).
- **Independent reviewer evaluation is small** (n = 6 across two rounds), author-facilitated, and non-domain-expert.
- **BM25 fallback affected the headline retrieval result** (Evidence Recall@5 73.9% in the reproducibility environment vs. 85% in the dev-phase dense run); the dissertation reports both numbers and clearly distinguishes them.
- **Generative arm of the adversarial probe** requires an OpenAI account with credit; the submission reports it as `n/a` honestly rather than fabricating the cells.

## 7. Quick sanity checks

If you only have five minutes:

```bash
# Confirm the package imports on a clean venv
python3 -m venv /tmp/pc && source /tmp/pc/bin/activate
pip install -e ".[dev]" >/dev/null
python -c "import policy_copilot; print(policy_copilot.__version__)"

# Confirm tests pass
pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py

# Confirm offline reproduction completes
python scripts/reproduce_offline.py
python scripts/verify_artifacts.py
```

That covers import, tests, offline reproduction, and artefact verification in one short loop.

## 8. Where to look first

- For metric values quoted in the report → `docs/evidence/checklist.md` maps each claim to the file that backs it.
- For an end-to-end audit trail → `docs/evidence/verification/audit_export_*.md` (three real cases lifted verbatim from the B3-Generative final run).
- For the human-evaluation results → `docs/evidence/human_eval/` (rubric, consent, anonymised scores, Krippendorff α).
- For the dissertation itself → `docs/report/Final_Report_Draft.pdf`.

## 9. Reporting issues

If a reproduction step fails on a reasonable environment, please open a GitHub issue describing:

- the operating system and Python version,
- the exact command that failed,
- the last 30 lines of error output,
- whether `pip install -e ".[dev]"` succeeded.

Do **not** include API keys or any personal data in the issue.
