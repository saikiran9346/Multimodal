import json

from app.retrieval.vector_store import upsert_chunks, search_hybrid
from app.retrieval.reranker import rerank


def load_all_chunks():
    with open("test_chunks.json", "r", encoding="utf-8") as f:
        text_chunks = json.load(f)
    with open("test_image_chunks.json", "r", encoding="utf-8") as f:
        image_chunks = json.load(f)

    print(f"Loaded {len(text_chunks)} text/table chunks and {len(image_chunks)} image chunks")
    return text_chunks + image_chunks


def print_results(label, results, score_key):
    print(f"\n=== {label} ===")
    for r in results:
        doc_name = r.get("doc_name", "document.pdf")
        content_types = r.get("content_types", ["text"])
        print(f"Score: {r[score_key]:.4f} | Doc: {doc_name} | Types: {content_types} | Page: {r['page_no']} | Headings: {r['headings']}")
        print(f"  {r['text'][:200]}")


def main():
    chunks = load_all_chunks()

    print(f"\nUpserting {len(chunks)} total chunks into Qdrant...")
    upsert_chunks(chunks, doc_name="grundfos_cm_pump_manual.pdf", recreate=True)
    print("Done.\n")

    query = "How is the pump connected in the terminal box, and what does the wiring diagram show?"
    print(f"Query: {query}")

    hybrid_results = search_hybrid(query, top_k=10)
    hybrid_dicts = [dict(p.payload, hybrid_score=p.score) for p in hybrid_results]
    print_results("Hybrid (RRF), top 10", hybrid_dicts, "hybrid_score")

    reranked = rerank(query, hybrid_dicts, top_k=5)
    print_results("After reranking, top 5", reranked, "rerank_score")


if __name__ == "__main__":
    main()