import glob
import json
import os

from docling_core.types.doc.document import DoclingDocument
from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk_document

CACHE_PATH = "test_parsed_doc.json"


def get_document(pdf_path: str):
    if os.path.exists(CACHE_PATH):
        print(f"Loading cached parsed document from {CACHE_PATH}")
        return DoclingDocument.load_from_json(CACHE_PATH)

    print(f"Parsing: {pdf_path}")
    document = parse_pdf(pdf_path)
    document.save_as_json(CACHE_PATH)
    return document


def main():
    manuals_dir = os.path.join("..", "data", "sample_manuals")
    pdf_files = glob.glob(os.path.join(manuals_dir, "*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {manuals_dir}")
        return

    document = get_document(pdf_files[0])

    print("Chunking...")
    chunks = chunk_document(document)
    print(f"\nTotal chunks: {len(chunks)}\n")

    output_path = "test_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Full chunk list saved to: {output_path}")


if __name__ == "__main__":
    main()