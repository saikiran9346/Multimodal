import os
import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from typing import List, Optional

from app.models.document import IngestResponse
from app.ingestion.parser import parse_document
from app.ingestion.chunker import chunk_document
from app.ingestion.image_processor import extract_image_chunks
from app.retrieval.vector_store import upsert_chunks, _get_client, COLLECTION_NAME, ensure_collection_exists
from qdrant_client.models import Filter, FieldCondition, MatchValue

router = APIRouter()


@router.get("/documents", tags=["Document Ingestion"])
def list_documents(x_session_id: Optional[str] = Header(default=None)):
    """
    Returns all unique documents indexed in the current session.
    Pass X-Session-ID header to scope results to a session.
    """
    try:
        ensure_collection_exists()
        client = _get_client()
        docs = {}
        offset = None
        while True:
            result, next_offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=500,
                with_payload=["doc_name", "session_id"],
                offset=offset,
            )
            for point in result:
                if not point.payload:
                    continue
                point_session = point.payload.get("session_id")
                # Filter by session if provided
                if x_session_id and point_session != x_session_id:
                    continue
                name = point.payload.get("doc_name", "unknown")
                docs[name] = docs.get(name, 0) + 1
            if next_offset is None:
                break
            offset = next_offset
        return {
            "documents": [
                {"doc_name": name, "chunk_count": count}
                for name, count in sorted(docs.items())
            ],
            "total_documents": len(docs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_name:path}", tags=["Document Ingestion"])
def delete_document(
    doc_name: str,
    x_session_id: Optional[str] = Header(default=None),
):
    """
    Deletes all indexed chunks for a document, scoped to the session if X-Session-ID is provided.
    """
    try:
        ensure_collection_exists()
        client = _get_client()
        conditions = [FieldCondition(key="doc_name", match=MatchValue(value=doc_name))]
        if x_session_id:
            conditions.append(FieldCondition(key="session_id", match=MatchValue(value=x_session_id)))
        doc_filter = Filter(must=conditions)
        count_before = client.count(collection_name=COLLECTION_NAME, count_filter=doc_filter).count
        if count_before == 0:
            raise HTTPException(status_code=404, detail=f"Document '{doc_name}' not found in the index.")
        client.delete(collection_name=COLLECTION_NAME, points_selector=doc_filter)
        return {"status": "deleted", "doc_name": doc_name, "chunks_removed": count_before}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

ALLOWED_EXTENSIONS = {
    # Documents
    ".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".md", ".csv",
    ".odt", ".ods", ".odp", ".tex", ".adoc", ".asciidoc",
    # Code & Configs
    ".py", ".js", ".ts", ".c", ".cpp", ".java", ".go", ".rs", ".sh",
    ".json", ".yaml", ".yml", ".txt", ".log", ".xml",
    # Images & Schematics
    ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
}


@router.post("/ingest", response_model=IngestResponse)
def ingest_document(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(default=None),
):
    """
    Ingests technical documents across 25+ file formats:
    - Documents: PDF, DOCX, PPTX, XLSX, HTML, MD, CSV, ODT, ODS, ODP, TEX, ADOC
    - Code & Configs: PY, JS, TS, C, CPP, JAVA, GO, RS, SH, JSON, YAML, TXT, XML
    - Images: PNG, JPG, JPEG, TIFF, BMP
    """
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if not filename or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported technical formats include PDF, Office, Code, Markdown, HTML, Data, and Images."
        )

    temp_dir = Path(tempfile.gettempdir()) / "multimodal_rag_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / filename

    try:
        # Save uploaded file to temp disk
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check for 0-byte / empty file
        if temp_file_path.stat().st_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

        # 1. Parse Document with Docling, catching corrupt/invalid formats as clean 400 Bad Request
        try:
            document = parse_document(str(temp_file_path))
        except HTTPException:
            raise
        except Exception as parse_err:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse '{filename}'. Please ensure it is a valid, uncorrupted document. Details: {str(parse_err)}"
            )

        # 2. Chunk text and tables
        text_chunks = chunk_document(document)

        # 3. Extract and describe diagrams/images
        image_chunks_path = str(temp_dir / f"{file.filename}_image_chunks.json")
        image_progress_path = str(temp_dir / f"{file.filename}_image_progress.json")
        image_chunks = extract_image_chunks(
            document,
            file_path=str(temp_file_path),
            chunks_path=image_chunks_path,
            progress_path=image_progress_path,
        )

        all_chunks = text_chunks + image_chunks

        # Tag each chunk with its document filename
        for chunk in all_chunks:
            chunk["doc_name"] = file.filename

        # 4. Upsert into Qdrant (recreate=False allows multiple documents to coexist)
        total_upserted = upsert_chunks(
            all_chunks,
            doc_name=file.filename,
            recreate=False,
            session_id=x_session_id,
        )

        return IngestResponse(
            status="success",
            filename=file.filename,
            total_chunks=total_upserted,
            text_chunks=len(text_chunks),
            image_chunks=len(image_chunks),
            message=f"Successfully indexed {len(all_chunks)} chunks for '{file.filename}' into Qdrant.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion processing failed: {str(e)}")
    finally:
        # Clean up temporary upload file
        if temp_file_path.exists():
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
