import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile

def log(msg):
    print(msg, flush=True)

# Copy cached image chunks directly to tempfile.gettempdir() where image_processor expects it
temp_base = tempfile.gettempdir()
if os.path.exists("test_image_chunks.json"):
    cache_dest = os.path.join(temp_base, "grundfos_cm_pump_manual.pdf_image_chunks.json")
    shutil.copy("test_image_chunks.json", cache_dest)
    log(f"Cached image chunks copied to {cache_dest}")

from app.api.routes.ingest import ingest_document
from app.api.routes.query import query_manual
from app.models.response import QueryRequest
from app.retrieval.vector_store import _get_client, COLLECTION_NAME

report = {"ingestion": [], "qdrant_counts": {}, "checks": []}

def save_report():
    with open("verification_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

pdf_path = os.path.abspath(os.path.join("..", "data", "sample_manuals", "grundfos_cm_pump_manual.pdf"))
docx_path = os.path.abspath("service_protocol.docx")
py_path = os.path.abspath("hydraulic_calculations.py")
img_path = os.path.abspath("fig9_wiring_diagram.png")

files_to_ingest = [
    ("grundfos_cm_pump_manual.pdf", pdf_path, "application/pdf"),
    ("service_protocol.docx", docx_path, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("hydraulic_calculations.py", py_path, "text/x-python"),
    ("fig9_wiring_diagram.png", img_path, "image/png"),
]

log("Ingesting 4 multi-category documents via FastAPI /api/ingest route...")

for filename, path, mime in files_to_ingest:
    with open(path, "rb") as f:
        content = f.read()
    upload_file = UploadFile(filename=filename, file=BytesIO(content))
    
    # Ingest document through FastAPI endpoint
    res = ingest_document(upload_file)
    report["ingestion"].append({"filename": filename, "status": res.status, "total_chunks": res.total_chunks})
    log(f"  • Ingested {filename:<32} -> {res.total_chunks} chunks")

save_report()

log("\nQuerying Qdrant collection directly for point counts per doc_name...")
q_client = _get_client()
collection_info = q_client.get_collection(COLLECTION_NAME)
report["total_qdrant_points"] = collection_info.points_count

points, _ = q_client.scroll(collection_name=COLLECTION_NAME, limit=2000, with_payload=True, with_vectors=False)
doc_counts = {}
for pt in points:
    doc = pt.payload.get("doc_name", "UNKNOWN")
    doc_counts[doc] = doc_counts.get(doc, 0) + 1

report["qdrant_counts"] = doc_counts
save_report()

for doc, count in sorted(doc_counts.items()):
    log(f"  • Qdrant doc_name '{doc:<32}' : {count} points")


def run_and_store_check(check_num, title, query, doc_name=None):
    log(f"\nExecuting Check {check_num}: {title}...")
    req = QueryRequest(query=query, top_k=5, exclude_images=False, doc_name=doc_name)
    res = query_manual(req)
    
    check_item = {
        "check_num": check_num,
        "title": title,
        "query": query,
        "doc_name_filter": doc_name,
        "llm_answer": res.answer,
        "sources": [
            {
                "index": s["index"],
                "doc_name": s.get("doc_name"),
                "page_no": s.get("page_no"),
                "headings": s.get("headings"),
                "content_types": s.get("content_types"),
                "score": s.get("score"),
                "text": s.get("text")
            }
            for s in res.sources
        ]
    }
    report["checks"].append(check_item)
    save_report()
    log(f"Check {check_num} Done!")


run_and_store_check(
    2,
    "PDF-ONLY QUERY (Must show real page_no)",
    "What is the maximum system pressure for a cast iron pump with shaft seal type AVBx?",
    doc_name="grundfos_cm_pump_manual.pdf"
)

run_and_store_check(
    3,
    "DOCX-ONLY QUERY (Must use heading fallback, no page_no, no literal 'None')",
    "What is the minimum acceptable winding insulation resistance when measured at 500V DC megohmmeter?",
    doc_name="service_protocol.docx"
)

run_and_store_check(
    4,
    "PYTHON CODE-ONLY QUERY (Report actual chunk boundaries and citation format)",
    "What formula is used in Python to calculate Net Positive Suction Head Available (NPSHa)?",
    doc_name="hydraulic_calculations.py"
)

run_and_store_check(
    5,
    "STANDALONE IMAGE QUERY (Report citation for source with no page, no heading, 1 chunk)",
    "What electrical wiring diagram or motor connection layout is shown in fig9_wiring_diagram.png?",
    doc_name="fig9_wiring_diagram.png"
)

log("\nALL 5 CHECKS COMPLETED AND SAVED TO verification_report.json!")
