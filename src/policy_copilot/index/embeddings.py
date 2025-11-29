from typing import List, Any
import numpy as np
from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

_model_instance = None
_sentence_transformer_cls = None

