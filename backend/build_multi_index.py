import json
from app.retrieval.vector_store import upsert_chunks, recreate_collection, _get_client, COLLECTION_NAME


def load_chunks(text_path, image_path, doc_name):
    chunks = []
    with open(text_path, "r", encoding="utf-8") as f:
        text_chunks = json.load(f)
    for c in text_chunks:
        c["doc_name"] = doc_name
    chunks.extend(text_chunks)

    with open(image_path, "r", encoding="utf-8") as f:
        image_chunks = json.load(f)
    for c in image_chunks:
        c["doc_name"] = doc_name
    chunks.extend(image_chunks)

    print(f"Loaded {len(text_chunks)} text chunks + {len(image_chunks)} image chunks for {doc_name}")
    return chunks


def main():
    print("Recreating Qdrant collection for Multi-PDF index...")
    recreate_collection()

    cm_chunks = load_chunks("test_chunks.json", "test_image_chunks.json", "grundfos_cm_pump_manual.pdf")
    tp_chunks = load_chunks("tp_chunks.json", "tp_image_chunks.json", "1_TP.pdf")

    all_chunks = cm_chunks + tp_chunks
    print(f"\nUpserting {len(all_chunks)} total chunks into Qdrant across 2 manuals...")
    upsert_chunks(all_chunks, recreate=False)

    client = _get_client()
    info = client.get_collection(COLLECTION_NAME)
    print(f"\nSuccessfully indexed {info.points_count} points into Qdrant!")


if __name__ == "__main__":
    main()
