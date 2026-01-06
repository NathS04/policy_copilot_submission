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

        self.backend_requested = requested
        self.backend_used = requested  # will be mutated on fallback

        if requested == "dense":
            try:
                from policy_copilot.index.faiss_index import FaissIndex
                self.dense_index = FaissIndex()
                self.dense_index.load(index_dir)
                self.loaded = True
                self.backend_used = "dense"
            except ImportError:
                logger.warning("Dense backend requested but dependencies missing. Falling back to BM25.")
                self.backend_used = "bm25"
            except Exception as e:
                logger.warning(f"Could not load FAISS index from {index_dir}: {e}. Falling back to BM25.")
                self.backend_used = "bm25"

        if self.backend_used == "bm25":
            self.loaded = self._init_bm25_backend()
