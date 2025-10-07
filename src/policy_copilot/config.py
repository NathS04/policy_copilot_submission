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
    # API keys
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

    # paths
    DATA_DIR: Path = Path("data")
    RAW_CORPUS_DIR: Path = Path("data/corpus/raw")
    UPLOADS_DIR: Path = Path("data/corpus/raw/uploads")
    CORPUS_DIR: Path = Path("data/corpus/processed")
    PROCESSED_DATA_DIR: Path = Path("data/corpus/processed")
    CORPUS_JSONL: Path = Path("data/corpus/processed/paragraphs.jsonl")
    INDEX_DIR: Path = Path("data/corpus/processed/index")
    MANIFEST_PATH: Path = Path("data/corpus/manifests/corpus_manifest.csv")
    GOLDEN_SET_PATH: Path = Path("eval/golden_set/golden_set.csv")

    # embedding model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
