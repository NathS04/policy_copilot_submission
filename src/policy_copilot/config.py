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

    # LLM settings
    PROVIDER: str = _json_cfg.get("provider", os.getenv("LLM_PROVIDER", "openai"))
    LLM_MODEL: str = _json_cfg.get("model_name", os.getenv("LLM_MODEL", "gpt-4o-mini"))
    TEMPERATURE: float = float(_json_cfg.get("temperature", os.getenv("LLM_TEMPERATURE", "0.0")))
    MAX_TOKENS: int = int(_json_cfg.get("max_tokens", os.getenv("LLM_MAX_TOKENS", "600")))
    TOP_K: int = int(_json_cfg.get("top_k", os.getenv("TOP_K", "5")))
    SEED: int = int(_json_cfg.get("seed", os.getenv("SEED", "42")))
    ENABLE_LLM: bool = _bool_from_cfg("enable_llm", "true")

    # --- Phase 4: B3 reliability settings ---
    RETRIEVE_K_CANDIDATES: int = int(_json_cfg.get("retrieve_k_candidates", os.getenv("RETRIEVE_K_CANDIDATES", "20")))
    RERANK_K_FINAL: int = int(_json_cfg.get("rerank_k_final", os.getenv("RERANK_K_FINAL", "5")))
    RERANK_MODEL: str = _json_cfg.get("rerank_model", os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"))
    ABSTAIN_THRESHOLD: float = float(_json_cfg.get("abstain_threshold", os.getenv("ABSTAIN_THRESHOLD", "0.30")))
    MIN_SUPPORT_RATE: float = float(_json_cfg.get("min_support_rate", os.getenv("MIN_SUPPORT_RATE", "0.80")))
    ENABLE_LLM_VERIFY: bool = _bool_from_cfg("enable_llm_verify", "false")
    ENABLE_LLM_CONTRADICTIONS: bool = _bool_from_cfg("enable_llm_contradictions", "false")
    CONTRADICTION_POLICY: str = _json_cfg.get("contradiction_policy", os.getenv("CONTRADICTION_POLICY", "surface"))

    # run tracking
    RUN_NAME: str = _json_cfg.get("run_name", os.getenv("RUN_NAME", datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")))
    OUTPUT_DIR: str = ""  # computed below

    def get_output_dir(self, run_name: str | None = None) -> Path:
        name = run_name or self.RUN_NAME
        return Path("results/runs") / name

    def to_dict(self) -> dict:
        """Serialisable snapshot of effective config (no secrets)."""
        return {
            "provider": self.PROVIDER,
            "model": self.LLM_MODEL,
            "temperature": self.TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
            "top_k": self.TOP_K,
            "seed": self.SEED,
            "enable_llm": self.ENABLE_LLM,
            "embedding_model": self.EMBEDDING_MODEL,
            "run_name": self.RUN_NAME,
            "retrieve_k_candidates": self.RETRIEVE_K_CANDIDATES,
            "rerank_k_final": self.RERANK_K_FINAL,
            "rerank_model": self.RERANK_MODEL,
            "abstain_threshold": self.ABSTAIN_THRESHOLD,
            "min_support_rate": self.MIN_SUPPORT_RATE,
            "enable_llm_verify": self.ENABLE_LLM_VERIFY,
            "enable_llm_contradictions": self.ENABLE_LLM_CONTRADICTIONS,
            "contradiction_policy": self.CONTRADICTION_POLICY,
        }


settings = Settings()
