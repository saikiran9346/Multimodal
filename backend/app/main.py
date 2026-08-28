from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.query import router as query_router
from app.api.routes.ingest import router as ingest_router
from app.retrieval.vector_store import _get_client, COLLECTION_NAME

app = FastAPI(
    title="Multimodal Technical Manual RAG API",
    description="Production-grade RAG backend with Hybrid Search (BM25 + Dense BGE), Cross-Encoder Reranking, Multimodal Diagram Understanding, and Groq LLM grounded citations.",
    version="1.0.0",
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(query_router, prefix="/api", tags=["Retrieval & Generation"])
app.include_router(ingest_router, prefix="/api", tags=["Document Ingestion"])


@app.get("/api/health", tags=["Health"])
def health_check():
    """
    Health check endpoint verifying FastAPI and Qdrant connectivity.
    """
    qdrant_status = "unreachable"
    indexed_points = 0
    try:
        client = _get_client()
        if client.collection_exists(COLLECTION_NAME):
            qdrant_status = "connected"
            collection_info = client.get_collection(COLLECTION_NAME)
            indexed_points = collection_info.points_count
        else:
            qdrant_status = "connected (no collection yet)"
    except Exception as e:
        qdrant_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "qdrant": qdrant_status,
        "indexed_chunks": indexed_points,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
