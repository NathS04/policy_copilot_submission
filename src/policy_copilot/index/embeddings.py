from typing import List, Any
import numpy as np
from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

_model_instance = None
_sentence_transformer_cls = None

def _try_import_sentence_transformers():
    """Lazily import SentenceTransformer or raise friendly error."""
    global _sentence_transformer_cls
    if _sentence_transformer_cls:
        return _sentence_transformer_cls
