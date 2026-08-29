import json

from app.retrieval.vector_store import upsert_chunks, search_dense, search_sparse, search_hybrid


def print_results(label, results):
    print(f"\n=== {label} ===")
    for point in results:
        print(f"Score: {point.score:.4f} | Page: {point.payload['page_no']} | Headings: {point.payload['headings']}")
        print(f"  {point.payload['text'][:150]}")


def main():
    with open("test_chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Upserting {len(chunks)} chunks (dense + sparse)...")
    count = upsert_chunks(chunks)
    print(f"Upserted {count} points.")

    query = "What is shaft seal type AQQx rated for?"
    print(f"\nQuery: {query}")

    print_results("Dense only", search_dense(query, top_k=3))
    print_results("Sparse (BM25) only", search_sparse(query, top_k=3))
    print_results("Hybrid (RRF fusion)", search_hybrid(query, top_k=3))


if __name__ == "__main__":
    main()