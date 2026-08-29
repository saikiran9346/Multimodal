import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile

# Ensure image chunks cache is copied to temp_dir before ingest so it runs in seconds
temp_dir = Path(tempfile.gettempdir()) / "multimodal_rag_uploads"
temp_dir.mkdir(parents=True, exist_ok=True)

if os.path.exists("test_image_chunks.json"):
    shutil.copy("test_image_chunks.json", temp_dir / "grundfos_cm_pump_manual.pdf_image_chunks.json")

from app.api.routes.ingest import ingest_document
from app.api.routes.query import query_manual
from app.models.response import QueryRequest
from app.retrieval.vector_store import _get_client, COLLECTION_NAME

out_file = open("verify_results.txt", "w", encoding="utf-8")

def p(*args, **kwargs):
    text = " ".join(str(a) for a in args)
    print(text)
    out_file.write(text + "\n")
    out_file.flush()
    sys.stdout.flush()

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

p("=" * 85)
p("1. INGESTING ALL 4 MULTI-CATEGORY DOCUMENTS VIA FASTAPI /api/ingest ROUTE")
p("=" * 85)

for filename, path, mime in files_to_ingest:
    with open(path, "rb") as f:
        content = f.read()
    upload_file = UploadFile(filename=filename, file=BytesIO(content))
    res = ingest_document(upload_file)
    p(f"Ingested: {filename:<32} | Status: {res.status} | Total Chunks: {res.total_chunks}")

p("\n" + "=" * 85)
p("CHECK 1: DIRECT QDRANT POINT COUNT BROKEN DOWN BY doc_name")
p("=" * 85)

q_client = _get_client()
collection_info = q_client.get_collection(COLLECTION_NAME)
total_points = collection_info.points_count
p(f"Total Points in Qdrant Collection '{COLLECTION_NAME}': {total_points}")

points, _ = q_client.scroll(collection_name=COLLECTION_NAME, limit=2000, with_payload=True, with_vectors=False)
doc_counts = {}
for pt in points:
    doc = pt.payload.get("doc_name", "UNKNOWN")
    doc_counts[doc] = doc_counts.get(doc, 0) + 1

for doc_name, count in sorted(doc_counts.items()):
    p(f"  • {doc_name:<35} : {count} points")


def run_and_print_query(check_num, title, query, doc_name=None):
    p("\n" + "=" * 85)
    p(f"CHECK {check_num}: {title}")
    p("=" * 85)
    p(f"Query: \"{query}\"")
    if doc_name:
        p(f"Document Filter: \"{doc_name}\"")
    
    req = QueryRequest(query=query, top_k=5, exclude_images=False, doc_name=doc_name)
    res = query_manual(req)
    
    p("\n--- RAW LLM ANSWER ---")
    p(res.answer)
    
    p("\n--- RAW RETRIEVED SOURCES & CITATIONS ---")
    for s in res.sources:
        p(f"\n[Source {s['index']}]")
        p(f"  doc_name      : {s.get('doc_name')}")
        p(f"  page_no       : {s.get('page_no')}")
        p(f"  headings      : {s.get('headings')}")
        p(f"  content_types : {s.get('content_types')}")
        p(f"  score         : {s.get('score')}")
        p(f"  text snippet  :\n{s.get('text')}")


# CHECK 2: PDF-only query
run_and_print_query(
    2,
    "PDF-ONLY QUERY (Must show real page_no)",
    "What is the maximum system pressure for a cast iron pump with shaft seal type AVBx?",
    doc_name="grundfos_cm_pump_manual.pdf"
)

# CHECK 3: DOCX-only query
run_and_print_query(
    3,
    "DOCX-ONLY QUERY (Must use heading fallback, no page_no, no literal 'None')",
    "What is the minimum acceptable winding insulation resistance when measured at 500V DC megohmmeter?",
    doc_name="service_protocol.docx"
)

# CHECK 4: Python Code-only query
run_and_print_query(
    4,
    "PYTHON CODE-ONLY QUERY (Report actual chunk boundaries and citation format)",
    "What formula is used in Python to calculate Net Positive Suction Head Available (NPSHa)?",
    doc_name="hydraulic_calculations.py"
)

# CHECK 5: Standalone Image query
run_and_print_query(
    5,
    "STANDALONE IMAGE QUERY (Report citation for source with no page, no heading, 1 chunk)",
    "What electrical wiring diagram or motor connection layout is shown in fig9_wiring_diagram.png?",
    doc_name="fig9_wiring_diagram.png"
)

out_file.close()
p("ALL 5 CHECKS COMPLETED SUCCESSFULLY")
