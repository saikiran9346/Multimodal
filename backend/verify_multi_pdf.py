from app.retrieval.vector_store import _get_client, COLLECTION_NAME
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = _get_client()

total = client.count(collection_name=COLLECTION_NAME).count
print(f"Total points in collection: {total}")

for doc_name in ["grundfos_cm_pump_manual.pdf", "1_TP.pdf"]:
    count = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(must=[FieldCondition(key="doc_name", match=MatchValue(value=doc_name))]),
    ).count
    print(f"  {doc_name}: {count} chunks")
