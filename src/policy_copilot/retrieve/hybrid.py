class HybridRetriever:
    def __init__(self, dense_retriever, sparse_retriever):
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        
    def retrieve(self, query: str, k: int = 5):
        # TODO: Implement hybrid fusion (RRF or weighted sum)
        return self.dense.retrieve(query, k)
