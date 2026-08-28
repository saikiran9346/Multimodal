from fastapi import APIRouter, HTTPException
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.models.response import QueryRequest, QueryResponse
from app.models.chunk import SourceChunk
from app.retrieval.vector_store import (
    search_hybrid, _get_client, COLLECTION_NAME, ensure_collection_exists, detect_document_from_query
)
from app.retrieval.reranker import rerank
from app.generation.llm import generate_grounded_answer

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_manual(request: QueryRequest):
    """
    End-to-end RAG query endpoint:
    1. Validates query text
    2. Validates document existence if doc_name filter is requested
    3. Hybrid search (Dense + BM25 with RRF)
    4. Cross-Encoder reranking
    5. Grounded answer generation via Groq LLM with citations
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        ensure_collection_exists()
        client = _get_client()

        # Document routing: explicit request.doc_name or detected from query text
        active_doc_name = request.doc_name or detect_document_from_query(request.query)

        # If an explicit doc_name was requested, verify it exists in the collection
        if request.doc_name:
            doc_filter = Filter(must=[FieldCondition(key="doc_name", match=MatchValue(value=request.doc_name))])
            doc_count = client.count(collection_name=COLLECTION_NAME, count_filter=doc_filter).count
            if doc_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document '{request.doc_name}' was not found in the indexed collection."
                )

        # Retrieve candidate chunks (fetch 3x top_k for reranking pool)
        retrieve_k = max(request.top_k * 3, 15)
        hybrid_points = search_hybrid(
            query=request.query,
            top_k=retrieve_k,
            exclude_images=request.exclude_images,
            doc_name=active_doc_name,
        )

        if not hybrid_points:
            return QueryResponse(
                query=request.query,
                answer="No relevant information found in the document index.",
                sources=[],
            )

        candidate_dicts = [
            dict(p.payload, hybrid_score=p.score)
            for p in hybrid_points
        ]

        # Rerank candidates with cross-encoder
        reranked_chunks = rerank(
            query=request.query,
            candidates=candidate_dicts,
            top_k=request.top_k,
        )

        # Generate grounded answer with Groq LLM
        grounded_result = generate_grounded_answer(
            question=request.query,
            chunks=reranked_chunks,
        )

        sources = [
            SourceChunk(
                index=i,
                doc_name=c.get("doc_name"),
                page_no=c.get("page_no"),
                headings=c.get("headings", []),
                content_types=c.get("content_types", ["text"]),
                text=c.get("text"),
                score=c.get("rerank_score", c.get("hybrid_score")),
            )
            for i, c in enumerate(reranked_chunks, start=1)
        ]

        return QueryResponse(
            query=request.query,
            answer=grounded_result["answer"],
            sources=sources,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
