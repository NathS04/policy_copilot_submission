from policy_copilot.retrieve.retriever import Retriever
from policy_copilot.rerank.reranker import Reranker
import pandas as pd

def main():
    df = pd.read_csv("eval/golden_set/golden_set_frozen_v1.csv")
    dev = df[df.split=="dev"]
    if dev.empty:
        print("No dev queries found")
        return
        
    row = dev.iloc[0]
    qid, question = row.query_id, row.question
    
    print(f"Query {qid}: {question}")
    
    retriever = Retriever()
    candidates = retriever.retrieve(question, k=20)
    
    reranker = Reranker()
    ranked = reranker.rerank(question, candidates)
    
    print("\nTop 5 Reranked:")
    for r in ranked:
        print(f"Score: {r['score']:.4f}  ID: {r['paragraph_id']}")
        print(f"Text: {r['text'][:100]}...")

if __name__ == "__main__":
    main()
