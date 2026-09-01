from fastapi import APIRouter, HTTPException
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.models.response import QueryRequest, QueryResponse, AgenticQueryResponse, CritiqueLogEntry
from app.models.chunk import SourceChunk
from app.retrieval.vector_store import (
    search_hybrid, _get_client, COLLECTION_NAME, ensure_collection_exists, detect_document_from_query
)
from app.retrieval.reranker import rerank
from app.generation.llm import generate_grounded_answer
from app.generation.critique import agentic_rag_pipeline

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
            filter_args = {"key": "doc_name", "match": MatchValue(value=request.doc_name)}
            doc_filter_conditions = [FieldCondition(**filter_args)]
            if request.session_id:
                doc_filter_conditions.append(
                    FieldCondition(key="session_id", match=MatchValue(value=request.session_id))
                )
            doc_filter = Filter(must=doc_filter_conditions)
            doc_count = client.count(collection_name=COLLECTION_NAME, count_filter=doc_filter).count
            if doc_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document '{request.doc_name}' was not found in the indexed collection."
                )

        # Retrieve candidate chunks (fetch 3x top_k for reranking pool)
        retrieve_k = max(request.top_k * 3, 30)
        hybrid_points = search_hybrid(
            query=request.query,
            top_k=retrieve_k,
            exclude_images=request.exclude_images,
            doc_name=active_doc_name,
            session_id=request.session_id,
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


@router.post("/query/agentic", response_model=AgenticQueryResponse)
def query_agentic(request: QueryRequest):
    """
    Self-Critique Adaptive Retrieval Agent endpoint:
    1. Standard RAG pipeline (hybrid search → rerank → generate)
    2. Critic LLM evaluates answer groundedness & completeness
    3. If confidence < 0.7: reformulate query → re-retrieve → re-generate
    4. Repeats up to 2 retries (max 3 total attempts)
    5. Returns final answer + full critique_log with reasoning trace
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = agentic_rag_pipeline(
            query=request.query,
            top_k=request.top_k,
            exclude_images=request.exclude_images,
            doc_name=request.doc_name,
            session_id=request.session_id,
            max_retries=2,
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
            for i, c in enumerate(result["sources"], start=1)
        ]

        critique_entries = [
            CritiqueLogEntry(**entry) for entry in result["critique_log"]
        ]

        return AgenticQueryResponse(
            query=request.query,
            answer=result["answer"],
            sources=sources,
            critique_log=critique_entries,
            attempts=result["attempts"],
            final_query=result["final_query"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

