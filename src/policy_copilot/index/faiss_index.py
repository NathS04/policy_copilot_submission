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
    
    def add(self, vectors: np.ndarray, metadata: List[Dict]):
        """
        Adds vectors and corresponding metadata to the index.
        """
        if len(vectors) != len(metadata):
            raise ValueError("Number of vectors and metadata items must match.")
        
        start_id = self.index.ntotal
        self.index.add(vectors)
        
        for i, meta in enumerate(metadata):
            self.docstore[start_id + i] = meta
            
    def search(self, query_vector: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Searches the index. returns (distances, indices, metadata_list)
        """
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
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "faiss.index"))
