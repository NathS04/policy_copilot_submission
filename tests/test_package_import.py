"""
Acceptance test: verify the package imports cleanly and exposes expected modules.
"""
import importlib
import pytest


EXPECTED_MODULES = [
    "policy_copilot",
    "policy_copilot.config",
    "policy_copilot.retrieve",
    "policy_copilot.retrieve.retriever",
    "policy_copilot.retrieve.bm25_retriever",
    "policy_copilot.retrieve.hybrid",
    "policy_copilot.generate",
    "policy_copilot.verify.claim_split",
    "policy_copilot.verify.citation_check",
    "policy_copilot.critic",
    "policy_copilot.service",
    "policy_copilot.service.schemas",
    "policy_copilot.service.chat_orchestrator",
    "policy_copilot.service.audit_report_service",
    "policy_copilot.service.run_inspector",
    "policy_copilot.service.reviewer_service",
]


@pytest.mark.parametrize("module_name", EXPECTED_MODULES)
def test_module_imports(module_name):
    """Every listed module must import without error."""
    mod = importlib.import_module(module_name)
    assert mod is not None


def test_version_attribute():
    """Package exposes __version__."""
    import policy_copilot
    assert hasattr(policy_copilot, "__version__")
    assert isinstance(policy_copilot.__version__, str)
