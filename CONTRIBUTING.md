# Contributing

This is a solo dissertation project for COMP3931 at the University of Leeds.
External contributions are not expected, but this document records the
development conventions used throughout the project.

## Development Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Code Quality

```bash
# Lint
ruff check src/ tests/ scripts/ eval/

# Type check
mypy src/policy_copilot/

# Test
pytest -q
```

## Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>
```

### Types

| Type | When to use |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behaviour change |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `chore` | Build, tooling, or housekeeping |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration |

### Scopes

| Scope | Area |
|---|---|
| `retrieval` | BM25, dense, hybrid retrieval |
| `rerank` | Cross-encoder reranking |
| `generate` | LLM answer generation |
| `verify` | Abstention, claim verification, contradictions |
| `critic` | L1-L6 policy language critic |
| `eval` | Evaluation harness, golden set, metrics |
| `ui` | Streamlit workbench |
| `service` | Orchestrator, audit reports, reviewer |
| `packaging` | pyproject.toml, dependencies, install |
| `research` | Literature review, search strategy |
| `docs` | Documentation |
| `repo` | Repository structure, CI, metadata |

### Examples

```
feat(retrieval): add reciprocal-rank fusion over bm25 and dense hits
fix(packaging): make build_index exit 2 when ML deps are absent
test(eval): add smoke coverage for offline reproduction
docs(research): add taxonomy and comparator matrix for related work
refactor(ui): split evidence rail rendering into reusable components
chore(repo): add CI workflow and issue templates
```

## Branch Naming

```
feat/<short-description>
fix/<short-description>
docs/<short-description>
refactor/<short-description>
```

## Testing

All tests must pass before merging to `main`:

```bash
pytest -q --ignore=tests/test_run_eval_requires_key_in_generative.py
```

The ignored test requires API keys and is run separately in online mode.
