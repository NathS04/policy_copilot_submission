from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional

from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


class BackendUnavailableError(RuntimeError):
    """Raised when a strictly-requested backend cannot be initialised
    and silent fallback is disabled (``allow_fallback=False``)."""


def _sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None


class Retriever:
    """Top-level retriever with explicit backend selection.

    Supported backends:
      - ``dense`` : FAISS over sentence-transformer embeddings.
      - ``bm25`` : Okapi BM25 over the same paragraphs.
      - ``hybrid`` : RRF-fused dense + BM25 (via HybridRetriever).
      - ``bm25_fallback`` : explicit opt-in name for runs that *intend* to
        document a BM25 fallback (used for historical runs and reproducibility).

    Backend provenance is recorded in five fields readable by callers:
      ``backend_requested``  (the original constructor argument)
      ``backend_used``       (what actually ran after init)
      ``backend_reason``     (``"explicit_request"`` / ``"explicit_fallback"`` /
                              ``"silent_fallback_dense_load_failed"`` /
                              ``"silent_fallback_dense_deps_missing"``)
      ``dense_index_path``   (path string if dense was loaded; else ``None``)
      ``dense_index_sha``    (SHA-256 of the FAISS index file if loaded; else ``None``)

    ``allow_fallback=False`` makes a failed dense load a hard error
    (``BackendUnavailableError``). ``allow_fallback=True`` (the default)
    preserves the historical behaviour of degrading to BM25 with a
    ``backend_reason`` that records why.
    """

    def __init__(
        self,
        index_dir: str = settings.INDEX_DIR,
        backend: str = "dense",
        allow_fallback: bool = True,
    ):
        self.loaded = False
        self.dense_index = None
        self.bm25_retriever = None
        self.hybrid_retriever = None

        # Determine requested backend (env override takes priority).
        env_backend = os.getenv("POLICY_COPILOT_BACKEND")
        if env_backend:
            logger.info(f"Retriever: Overriding backend to {env_backend} from environment.")
            requested = env_backend
        else:
            requested = backend

        self.backend_requested = requested
        self.backend_used = requested  # mutated on fallback
        self.backend_reason = "explicit_request"
        self.dense_index_path: Optional[str] = None
        self.dense_index_sha: Optional[str] = None

        self._index_dir = index_dir
        self._allow_fallback = bool(allow_fallback)

        if requested == "dense":
            self._init_dense_strict_or_fallback(index_dir)
        elif requested == "bm25":
            self.loaded = self._init_bm25_backend()
        elif requested == "bm25_fallback":
            # Named explicit opt-in for BM25 used as a documented fallback.
            self.backend_used = "bm25"
            self.backend_reason = "explicit_fallback"
            self.loaded = self._init_bm25_backend()
        elif requested == "hybrid":
            self._init_hybrid(index_dir)
        else:
            raise ValueError(
                f"Retriever: unknown backend {requested!r}. "
                "Use one of: 'dense', 'bm25', 'hybrid', 'bm25_fallback'."
            )

    @property
    def backend(self) -> str:
        """Alias for backend_used (preserved for callers throughout the codebase)."""
        return self.backend_used

    # ------------------------------------------------------------------ #
    # Internal init paths
    # ------------------------------------------------------------------ #

    def _init_dense_strict_or_fallback(self, index_dir: str) -> None:
        try:
            from policy_copilot.index.faiss_index import FaissIndex
            self.dense_index = FaissIndex()
            self.dense_index.load(index_dir)
            self.loaded = True
            self.backend_used = "dense"
            self.dense_index_path = str(index_dir)
            self.dense_index_sha = _sha256_file(Path(index_dir) / "faiss.index")
            return
        except ImportError as exc:
            reason_tag = "silent_fallback_dense_deps_missing"
            err_msg = str(exc)
        except Exception as exc:
            reason_tag = "silent_fallback_dense_load_failed"
            err_msg = str(exc)

        if not self._allow_fallback:
            raise BackendUnavailableError(
                f"Dense backend strictly requested but unavailable: {err_msg}"
            )
        logger.warning(
            "Dense backend requested but unavailable (%s). Falling back to BM25.",
            err_msg,
        )
        self.backend_used = "bm25"
        self.backend_reason = reason_tag
        self.loaded = self._init_bm25_backend()

    def _init_hybrid(self, index_dir: str) -> None:
        """Construct dense + BM25 and fuse via HybridRetriever (RRF)."""
        from policy_copilot.retrieve.bm25_retriever import BM25Retriever
        from policy_copilot.retrieve.hybrid import HybridRetriever

        # Dense side
        dense_inner = None
        try:
            from policy_copilot.index.faiss_index import FaissIndex
            fi = FaissIndex()
            fi.load(index_dir)
            # Wrap into a tiny adapter exposing .loaded and .retrieve
            dense_inner = _DenseAdapter(fi, index_dir)
            self.dense_index = fi
            self.dense_index_path = str(index_dir)
            self.dense_index_sha = _sha256_file(Path(index_dir) / "faiss.index")
        except Exception as exc:
            dense_load_err = str(exc)
            if not self._allow_fallback:
                raise BackendUnavailableError(
                    f"Hybrid backend: dense load failed ({dense_load_err}) and fallback disabled"
                )
            logger.warning("Hybrid: dense unavailable (%s); falling back to BM25-only.", dense_load_err)
            self.backend_used = "bm25"
            self.backend_reason = "silent_fallback_dense_load_failed"
            self.loaded = self._init_bm25_backend()
            return

        # Sparse side
        self.bm25_retriever = BM25Retriever()
        if not self.bm25_retriever.is_ready:
            raise BackendUnavailableError("Hybrid backend: BM25 init failed")

        # Phase 4: allow env-var overrides of RRF tuning knobs so the
        # alpha/k tradeoff can be swept without changing code.
        import os as _os
        try:
            _alpha = float(_os.environ.get("POLICY_COPILOT_HYBRID_ALPHA", "0.5"))
        except ValueError:
            _alpha = 0.5
        try:
            _rrf_k = int(_os.environ.get("POLICY_COPILOT_HYBRID_RRF_K", "60"))
        except ValueError:
            _rrf_k = 60
        self.hybrid_retriever = HybridRetriever(
            dense_retriever=dense_inner,
            sparse_retriever=self.bm25_retriever,
            alpha=_alpha,
            rrf_k=_rrf_k,
        )
        if not self.hybrid_retriever.loaded:
            raise BackendUnavailableError("Hybrid backend: neither side loaded")

        self.loaded = True
        self.backend_used = "hybrid"

    def _init_bm25_backend(self) -> bool:
        """Initialise BM25 backend if not already ready."""
        if self.bm25_retriever is not None and self.bm25_retriever.is_ready:
            return True
        try:
            from policy_copilot.retrieve.bm25_retriever import BM25Retriever
            self.bm25_retriever = BM25Retriever()
            return self.bm25_retriever.is_ready
        except Exception as e:
            logger.error(f"Failed to initialize BM25 backend: {e}")
            self.bm25_retriever = None
            return False

    # ------------------------------------------------------------------ #
    # retrieve()
    # ------------------------------------------------------------------ #

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        if not self.loaded:
            logger.error("Retriever not loaded.")
            return []

        if self.backend_used == "hybrid" and self.hybrid_retriever is not None:
            return self.hybrid_retriever.retrieve(query, k=k)

        if self.backend_used == "bm25" and self.bm25_retriever:
            return self.bm25_retriever.retrieve(query, k=k)

        from policy_copilot.index.embeddings import embed_texts

        try:
            query_vec = embed_texts([query])[0]
            distances, _, metas = self.dense_index.search(query_vec, k)
        except Exception as e:
            logger.error(f"Dense retrieval failed: {e}")
            if not self._allow_fallback:
                raise BackendUnavailableError(
                    f"Dense retrieval failed at runtime and fallback disabled: {e}"
                )
            logger.warning("Attempting runtime fallback to BM25 retriever.")
            if self._init_bm25_backend():
                self.backend_used = "bm25"
                self.backend_reason = "silent_fallback_dense_runtime_error"
                self.loaded = True
                return self.bm25_retriever.retrieve(query, k=k)
            return []

        results = []
        for dist, meta in zip(distances[0], metas):
            if meta:
                similarity = 1.0 / (1.0 + float(dist))
                results.append({
                    "score": similarity,
                    "dist_l2": float(dist),
                    "paragraph_id": meta.get("paragraph_id"),
                    "doc_id": meta.get("doc_id"),
                    "page": meta.get("page"),
                    "text": meta.get("text"),
                    "source_file": meta.get("source_file"),
                    "backend": "dense"
                })
        return results


class _DenseAdapter:
    """Tiny adapter so HybridRetriever can use FaissIndex via a uniform
    .retrieve(query, k=...) -> List[Dict] interface."""

    def __init__(self, faiss_index, index_dir):
        self._fi = faiss_index
        self._index_dir = index_dir
        self.loaded = True

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        from policy_copilot.index.embeddings import embed_texts
        query_vec = embed_texts([query])[0]
        distances, _, metas = self._fi.search(query_vec, k)
        out = []
        for dist, meta in zip(distances[0], metas):
            if meta:
                similarity = 1.0 / (1.0 + float(dist))
                out.append({
                    "score": similarity,
                    "dist_l2": float(dist),
                    "paragraph_id": meta.get("paragraph_id"),
                    "doc_id": meta.get("doc_id"),
                    "page": meta.get("page"),
                    "text": meta.get("text"),
                    "source_file": meta.get("source_file"),
                    "backend": "dense"
                })
        return out
