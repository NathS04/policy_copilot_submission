from typing import List, Dict
import os
from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

class Retriever:
    def __init__(self, index_dir: str = settings.INDEX_DIR, backend: str = "dense"):
        self.loaded = False
        self.dense_index = None
        self.bm25_retriever = None

        # Determine requested backend (env override takes priority)
        env_backend = os.getenv("POLICY_COPILOT_BACKEND")
        if env_backend:
            logger.info(f"Retriever: Overriding backend to {env_backend} from environment.")
            requested = env_backend
        else:
            requested = backend
