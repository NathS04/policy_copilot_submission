"""
CLI tool for querying the Policy Copilot.
Supports retrieval-only mode and optional LLM generation (--llm flag).
"""
import argparse
import sys

from policy_copilot.retrieve.retriever import Retriever
from policy_copilot.config import settings


def main():
    parser = argparse.ArgumentParser(description="Query the Policy Copilot.")
    parser.add_argument("query", help="The question to ask")
    parser.add_argument("--top_k", type=int, default=settings.TOP_K,
                        help="Number of paragraphs to retrieve")
    parser.add_argument("--llm", action="store_true",
                        help="Also generate an LLM answer (naive RAG)")
    args = parser.parse_args()

    print(f"Query: {args.query}")
    print("=" * 50)

    # --- retrieval ---
    retriever = Retriever()
    if not retriever.loaded:
        print("Error: Index not loaded. Run build_index.py first.")
        sys.exit(1)

    results = retriever.retrieve(args.query, k=args.top_k)

    print(f"\nTop-{args.top_k} Retrieved Evidence:")
    print("-" * 50)
    for i, res in enumerate(results, 1):
        print(f"Rank {i} | Score: {res['score']:.4f}")
        print(f"  Source: {res['doc_id']} (Page {res['page']})")
        print(f"  ID: {res['paragraph_id']}")
        snippet = res['text'][:500].replace('\n', ' ')
        print(f"  Text: {snippet}")
        print("-" * 50)

    # --- optional LLM generation ---
    if args.llm:
        print("\n" + "=" * 50)
        print("Generating LLM answer (Naive RAG)...")
        print("=" * 50)

        from policy_copilot.generate.answerer import Answerer
        answerer = Answerer()
        resp, meta = answerer.generate_naive_rag(args.query, results)

        print(f"\nAnswer: {resp.answer}")
        print(f"Citations: {resp.citations}")
        if resp.notes:
            print(f"Notes: {resp.notes}")
        print(f"Latency: {meta.get('latency_ms', 0):.0f}ms")
        print(f"Provider: {meta.get('provider', 'N/A')}")


if __name__ == "__main__":
    main()
