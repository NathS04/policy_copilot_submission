"""
Central config for the Policy Copilot project.
Loads from .env, then from an optional JSON config, then env-var overrides.
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ---- optional JSON config overlay ----
_CONFIG_PATH = Path("configs/run_config.json")

def _load_json_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

_json_cfg = _load_json_config()


def _bool_from_cfg(key: str, default: str = "true") -> bool:
    """Parse a boolean from the JSON config or env var."""
    raw = _json_cfg.get(key, os.getenv(key.upper(), default))
    if isinstance(raw, bool):
        return raw
    return str(raw).lower() in ("true", "1", "yes")


class Settings(BaseModel):
