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
