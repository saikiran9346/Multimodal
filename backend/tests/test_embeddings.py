import json
import numpy as np

from app.retrieval.embeddings import embed_passages, embed_query


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    with open("test_chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    vectors = embed_passages(texts)
    print(f"Embedding dimension: {len(vectors[0])}\n")

    query = "What does this manual describe and what pumps does it cover?"
    print(f"Query: {query}\n")
    query_vector = embed_query(query)

    scored = [
        (cosine_similarity(query_vector, vec), chunk)
        for vec, chunk in zip(vectors, chunks)
    ]
    scored.sort(key=lambda x: -x[0])

    print("Top 3 most similar chunks:")
    for score, chunk in scored[:3]:
        print(f"\nScore: {score:.4f}")
        print(f"Page: {chunk['page_no']}")
        print(f"Headings: {chunk['headings']}")
        print(f"Text: {chunk['text'][:200]}")


if __name__ == "__main__":
    main()