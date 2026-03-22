"""
Acceptance test: critical scripts must be runnable with --help / basic invocations.
"""
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def _run(args, timeout=15):
    return subprocess.run(
        [sys.executable] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


def test_run_eval_help():
    result = _run([str(SCRIPTS / "run_eval.py"), "--help"])
    assert result.returncode == 0
    assert "baseline" in result.stdout.lower()


def test_reproduce_offline():
    result = _run([str(SCRIPTS / "reproduce_offline.py")])
    assert result.returncode == 0


def test_verify_artifacts():
    result = _run([str(SCRIPTS / "verify_artifacts.py")])
    assert result.returncode == 0


def test_verify_artifacts_strict_detects_mismatch():
    """Strict mode must fail on backend_requested != backend_used in shipped runs."""
    result = _run([str(SCRIPTS / "verify_artifacts.py"), "--strict"])
    assert result.returncode != 0


def test_smoke_script_exists():
    """The smoke install script must exist and be executable."""
    smoke = SCRIPTS / "smoke_install.sh"
    assert smoke.exists()
    assert smoke.stat().st_mode & 0o111
