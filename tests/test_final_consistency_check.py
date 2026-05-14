"""Phase N test: the final consistency-check script must pass."""
from __future__ import annotations

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
