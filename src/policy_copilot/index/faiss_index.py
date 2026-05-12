import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

class FaissIndex:
    """Thin wrapper around a flat L2 FAISS index plus a parallel docstore.

    Flat L2 is plenty for a corpus this size; if the corpus grows past a
    few tens of thousands of paragraphs, swap to IVF/HNSW here.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.docstore: Dict[int, Dict] = {}  # FAISS id -> paragraph metadata

    def add(self, vectors: np.ndarray, metadata: List[Dict]):
        """Add vectors and their metadata to the index in lock-step."""
        if len(vectors) != len(metadata):
            raise ValueError("Number of vectors and metadata items must match.")

        start_id = self.index.ntotal
        self.index.add(vectors)

        for i, meta in enumerate(metadata):
            self.docstore[start_id + i] = meta

    def search(self, query_vector: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """Return (distances, indices, metadata_list) for the top-k neighbours."""
        distances, indices = self.index.search(query_vector.reshape(1, -1), k)

        results_meta = []
        for idx in indices[0]:
            if idx != -1:
                results_meta.append(self.docstore.get(idx, {}))
            else:
                results_meta.append({})

        return distances, indices, results_meta

    def save(self, path: Path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(path / "faiss.index"))

        with open(path / "docstore.jsonl", "w", encoding="utf-8") as f:
            for idx, meta in self.docstore.items():
                entry = {"faiss_id": idx, "meta": meta}
                f.write(json.dumps(entry) + "\n")

        with open(path / "index_meta.json", "w", encoding="utf-8") as f:
            json.dump({
                "dimension": self.dimension,
                "count": self.index.ntotal,
            }, f)

    def load(self, path: Path):
        path = Path(path)
        self.index = faiss.read_index(str(path / "faiss.index"))

        self.docstore = {}
        with open(path / "docstore.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                self.docstore[entry["faiss_id"]] = entry["meta"]

        logger.info(f"Loaded index with {self.index.ntotal} vectors.")
