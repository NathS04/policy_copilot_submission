from typing import List, Dict
import os
from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

class Retriever:
    def __init__(self, index_dir: str = settings.INDEX_DIR, backend: str = "dense"):
        self.loaded = False
