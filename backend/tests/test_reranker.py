import json

from app.retrieval.vector_store import upsert_chunks, search_hybrid
from app.retrieval.reranker import rerank


def point_to_dict(point):
    d = dict(point.payload)
    d["hybrid_score"] = point.score
    return d


def print_results(label, results, score_key):
    print(f"\n=== {label} ===")
    for r in results:
        print(f"Score: {r[score_key]:.4f} | Page: {r['page_no']} | Headings: {r['headings']}")
        print(f"  {r['text'][:150]}")


def main():
    with open("test_chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Upserting {len(chunks)} chunks...")
    upsert_chunks(chunks)

    query = "What is shaft seal type AQQx rated for?"
    print(f"\nQuery: {query}")

    hybrid_results = search_hybrid(query, top_k=10)
    hybrid_dicts = [point_to_dict(p) for p in hybrid_results]
    print_results("Hybrid (RRF), top 10 before reranking", hybrid_dicts, "hybrid_score")

    reranked = rerank(query, hybrid_dicts, top_k=5)
    print_results("After cross-encoder reranking, top 5", reranked, "rerank_score")


if __name__ == "__main__":
    main()