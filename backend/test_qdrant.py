import json

from app.retrieval.vector_store import upsert_chunks, search


def main():
    with open("test_chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Upserting {len(chunks)} chunks into Qdrant...")
    count = upsert_chunks(chunks)
    print(f"Upserted {count} points.\n")

    query = "What does this manual describe and what pumps does it cover?"
    print(f"Query: {query}\n")

    results = search(query, top_k=3)

    print("Top 3 results from Qdrant:")
    for point in results:
        print(f"\nScore: {point.score:.4f}")
        print(f"Page: {point.payload['page_no']}")
        print(f"Headings: {point.payload['headings']}")
        print(f"Text: {point.payload['text'][:200]}")


if __name__ == "__main__":
    main()