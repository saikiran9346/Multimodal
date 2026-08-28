from app.retrieval.vector_store import search_hybrid
from app.retrieval.reranker import rerank
from app.generation.llm import generate_grounded_answer


def main():
    query = "How is the pump connected in the terminal box, and what does the wiring diagram show?"
    print(f"Query: {query}\n")

    hybrid_results = search_hybrid(query, top_k=10)
    hybrid_dicts = [dict(p.payload, hybrid_score=p.score) for p in hybrid_results]

    reranked = rerank(query, hybrid_dicts, top_k=5)

    result = generate_grounded_answer(query, reranked)

    print("--- ANSWER ---")
    print(result["answer"])

    print("\n--- SOURCES ---")
    for s in result["sources"]:
        print(f"[{s['index']}] Page {s['page_no']} | Types: {s['content_types']} | {s['headings']}")


if __name__ == "__main__":
    main()