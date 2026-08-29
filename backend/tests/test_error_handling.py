import os
import json
import tempfile
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def print_result(test_num, title, response):
    print(f"\n{'='*70}")
    print(f"TEST {test_num}: {title}")
    print(f"{'='*70}")
    print(f"HTTP Status Code: {response.status_code}")
    try:
        body = response.json()
        print("Response Body:")
        print(json.dumps(body, indent=2))
    except Exception:
        print("Response Body (Raw Text):")
        print(response.text)


def main():
    print("=" * 70)
    print("FASTAPI BACKEND ERROR HANDLING TEST SUITE")
    print("=" * 70)

    # 1. Upload endpoint: .txt file renamed to .pdf (corrupted PDF content)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"This is just plain text content, not a valid PDF format.")
        fake_pdf_path = f.name
    try:
        with open(fake_pdf_path, "rb") as f:
            resp = client.post("/api/ingest", files={"file": ("fake_corrupted.pdf", f, "application/pdf")})
        print_result(1, "Corrupted/Fake PDF (.txt renamed to .pdf)", resp)
    finally:
        if os.path.exists(fake_pdf_path):
            os.remove(fake_pdf_path)

    # 2. Upload endpoint: genuinely empty file (0 bytes)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        empty_pdf_path = f.name
    try:
        with open(empty_pdf_path, "rb") as f:
            resp = client.post("/api/ingest", files={"file": ("empty.pdf", f, "application/pdf")})
        print_result(2, "Empty File (0 bytes)", resp)
    finally:
        if os.path.exists(empty_pdf_path):
            os.remove(empty_pdf_path)

    # 3. Upload endpoint: real image file (.jpg or .png)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
        png_path = f.name
    try:
        with open(png_path, "rb") as f:
            resp = client.post("/api/ingest", files={"file": ("diagram.png", f, "image/png")})
        print_result(3, "Image file (.png instead of .pdf)", resp)
    finally:
        if os.path.exists(png_path):
            os.remove(png_path)

    # 4. Upload endpoint: missing file field entirely
    resp = client.post("/api/ingest", data={"dummy": "data"})
    print_result(4, "Missing file field entirely", resp)

    # 5. Query endpoint: empty string question
    resp = client.post("/api/query", json={"query": ""})
    print_result(5, "Query with empty string ('')", resp)

    # 6. Query endpoint: missing query field
    resp = client.post("/api/query", json={"question": "What is the pump pressure?"})
    print_result(6, "Missing 'query' field in request body", resp)

    # 7. Query endpoint: filter by nonexistent document
    resp = client.post("/api/query", json={
        "query": "What is shaft seal type AQQx rated for?",
        "doc_name": "nonexistent_document_12345.pdf"
    })
    print_result(7, "Filter with non-existent document", resp)

    # 8. Query endpoint: query yielding 0 results (unmatched query on non-existent collection/doc)
    resp = client.post("/api/query", json={
        "query": "zyxwvutsrqponmlkjihgfedcba completely random string impossible to match",
        "doc_name": "nonexistent_doc.pdf"
    })
    print_result(8, "Query with 0 search matches", resp)

    # 9. Query endpoint: extremely long question (5000+ characters)
    long_query = "What are the technical specifications of the pump? " * 100
    resp = client.post("/api/query", json={"query": long_query})
    print_result(9, f"Extremely long query ({len(long_query)} chars)", resp)

    print("\n" + "=" * 70)
    print("ALL 9 ERROR HANDLING TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
