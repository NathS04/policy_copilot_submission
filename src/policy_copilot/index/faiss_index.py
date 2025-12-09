import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

class FaissIndex:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.docstore: Dict[int, Dict] = {} # maps ID (int) -> paragraph meta
