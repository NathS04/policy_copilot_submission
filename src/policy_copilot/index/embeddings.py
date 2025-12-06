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
        
    try:
        from sentence_transformers import SentenceTransformer
        _sentence_transformer_cls = SentenceTransformer
        return _sentence_transformer_cls
    except ImportError:
        raise RuntimeError(
            "sentence-transformers not installed. "
            "Install with `pip install -e .[ml]` to use dense embeddings."
        )

def get_embedding_model() -> Any:
    """
    Returns the singleton SentenceTransformer model.
    """
    global _model_instance
    if _model_instance is None:
        ST = _try_import_sentence_transformers()
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model_instance = ST(settings.EMBEDDING_MODEL)
    return _model_instance

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embeds a list of texts. Returns numpy array of shape (n, dim).
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    return embeddings
