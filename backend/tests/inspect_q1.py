from app.retrieval.vector_store import search_hybrid
from app.retrieval.reranker import rerank

query = "What does section 6 of this manual cover, and what are its subsections?"

hybrid_results = search_hybrid(query, top_k=10)
print("=== Hybrid top 10 ===")
for p in hybrid_results:
    print(f"Score: {p.score:.4f} | Page: {p.payload['page_no']} | Headings: {p.payload['headings']}")
    print(f"  {p.payload['text'][:150]}")

hybrid_dicts = [dict(p.payload, hybrid_score=p.score) for p in hybrid_results]
reranked = rerank(query, hybrid_dicts, top_k=5)
print("\n=== Reranked top 5 ===")
for c in reranked:
    print(f"Score: {c['rerank_score']:.4f} | Page: {c['page_no']} | Headings: {c['headings']}")
    print(f"  {c['text'][:150]}")