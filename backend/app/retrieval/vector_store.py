import uuid
import socket
from pathlib import Path
from typing import Optional

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, SparseVectorParams, SparseVector, PointStruct,
    Prefetch, FusionQuery, Fusion, Modifier, Filter, FieldCondition, MatchValue,
)

from app.config import settings
from app.retrieval.embeddings import embed_passages, embed_query

import re

COLLECTION_NAME = "manual_chunks"
VECTOR_SIZE = 768

_client = None
_sparse_model = None


def get_manual_display_name(doc_name: str) -> str:
    doc_lower = doc_name.lower()
    if "cm" in doc_lower:
        return "Grundfos CM, CME"
    elif "tp" in doc_lower:
        return "Grundfos TP, TPD"
    return doc_name.replace(".pdf", "").replace("_", " ")


def format_chunk_text(text: str, doc_name: str) -> str:
    if text.startswith("[Manual:"):
        return text
    manual_name = get_manual_display_name(doc_name)
    return f"[Manual: {manual_name}]\n{text}"


def detect_document_from_query(query: str) -> Optional[str]:
    """
    Detects if a user query explicitly mentions a specific manual or pump series.
    Returns the corresponding doc_name if explicitly identified in the query, else None.
    Does not guess or assume when ambiguous or generic.
    """
    q_lower = query.lower()
    # Check for TP / TPD pump mentions
    if re.search(r'\b(tp|tpd)\b', q_lower) or "tp manual" in q_lower:
        return "1_TP.pdf"
    
    # Check for CM / CME pump mentions
    if re.search(r'\b(cm|cme)\b', q_lower) or "cm manual" in q_lower or "grundfos cm" in q_lower:
        return "grundfos_cm_pump_manual.pdf"
        
    return None


def _is_qdrant_server_online(url: str) -> bool:
    try:
        host = "localhost"
        port = 6333
        if ":" in url:
            parts = url.split(":")
            if len(parts) == 3:
                host = parts[1].replace("//", "")
                port = int(parts[2].split("/")[0])
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        if _is_qdrant_server_online(settings.qdrant_url):
            _client = QdrantClient(url=settings.qdrant_url, check_compatibility=False)
        else:
            db_path = str(Path(__file__).resolve().parent.parent.parent / "qdrant_storage")
            _client = QdrantClient(path=db_path)
    return _client


def _get_sparse_model() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    return _sparse_model


def _to_sparse_vector(sparse_embedding) -> SparseVector:
    return SparseVector(
        indices=sparse_embedding.indices.tolist(),
        values=sparse_embedding.values.tolist(),
    )


def _build_filter(
    exclude_images: bool = False,
    doc_name: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Optional[Filter]:
    must = []
    must_not = []
    if exclude_images:
        must_not.append(FieldCondition(key="content_types", match=MatchValue(value="picture")))
    if doc_name:
        must.append(FieldCondition(key="doc_name", match=MatchValue(value=doc_name)))
    if session_id:
        must.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))
    if not must and not must_not:
        return None
    return Filter(must=must if must else None, must_not=must_not if must_not else None)


def ensure_collection_exists():
    client = _get_client()
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={"dense": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(modifier=Modifier.IDF)},
        )


def recreate_collection():
    client = _get_client()
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={"dense": VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)},
        sparse_vectors_config={"sparse": SparseVectorParams(modifier=Modifier.IDF)},
    )


def upsert_chunks(
    chunks: list[dict],
    doc_name: str = "document.pdf",
    recreate: bool = False,
    session_id: Optional[str] = None,
) -> int:
    if recreate:
        recreate_collection()
    else:
        ensure_collection_exists()

    client = _get_client()

    formatted_chunks = []
    for c in chunks:
        c_copy = dict(c)
        chunk_doc_name = c_copy.get("doc_name", doc_name)
        c_copy["doc_name"] = chunk_doc_name
        c_copy["text"] = format_chunk_text(c_copy["text"], chunk_doc_name)
        formatted_chunks.append(c_copy)

    texts = [c["text"] for c in formatted_chunks]
    dense_vectors = embed_passages(texts)
    sparse_vectors = list(_get_sparse_model().embed(texts))

    points = []
    for i, (dense_vec, sparse_vec, chunk) in enumerate(zip(dense_vectors, sparse_vectors, formatted_chunks)):
        chunk_doc_name = chunk["doc_name"]
        # Include session_id in point_id so same doc in different sessions gets separate points
        sid_prefix = session_id or "global"
        point_id = str(uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{sid_prefix}_{chunk_doc_name}_{chunk.get('page_no')}_{i}_{chunk['text'][:40]}"
        ))

        payload = {
            "doc_name": chunk_doc_name,
            "text": chunk["text"],
            "page_no": chunk["page_no"],
            "headings": chunk["headings"],
            "captions": chunk["captions"],
            "content_types": chunk["content_types"],
            "contains_table": chunk["contains_table"],
        }
        if session_id:
            payload["session_id"] = session_id

        points.append(
            PointStruct(
                id=point_id,
                vector={"dense": dense_vec, "sparse": _to_sparse_vector(sparse_vec)},
                payload=payload,
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search_dense(
    query: str,
    top_k: int = 5,
    exclude_images: bool = False,
    doc_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    client = _get_client()
    ensure_collection_exists()
    query_filter = _build_filter(exclude_images=exclude_images, doc_name=doc_name, session_id=session_id)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=embed_query(query),
        using="dense",
        limit=top_k,
        query_filter=query_filter,
    )
    return results.points


def search_sparse(
    query: str,
    top_k: int = 5,
    exclude_images: bool = False,
    doc_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    client = _get_client()
    ensure_collection_exists()
    sparse_vec = list(_get_sparse_model().embed([query]))[0]
    query_filter = _build_filter(exclude_images=exclude_images, doc_name=doc_name, session_id=session_id)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=_to_sparse_vector(sparse_vec),
        using="sparse",
        limit=top_k,
        query_filter=query_filter,
    )
    return results.points


def search_hybrid(
    query: str,
    top_k: int = 5,
    exclude_images: bool = False,
    doc_name: Optional[str] = None,
    session_id: Optional[str] = None,
):
    client = _get_client()
    ensure_collection_exists()
    sparse_vec = list(_get_sparse_model().embed([query]))[0]
    query_filter = _build_filter(exclude_images=exclude_images, doc_name=doc_name, session_id=session_id)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(query=embed_query(query), using="dense", limit=top_k * 2, filter=query_filter),
            Prefetch(query=_to_sparse_vector(sparse_vec), using="sparse", limit=top_k * 2, filter=query_filter),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
    )
    return results.points