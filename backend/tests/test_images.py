import glob
import json
import os

from docling_core.types.doc.document import DoclingDocument
from app.ingestion.parser import parse_pdf
from app.ingestion.image_processor import extract_image_chunks

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

    print(f"\nFound {len(document.pictures)} pictures in the document")
    print("Describing each with Groq vision -- one API call per image, this will take a bit:\n")

    image_chunks = extract_image_chunks(document)

    print(f"\nGot {len(image_chunks)} image descriptions\n")

    for i, chunk in enumerate(image_chunks[:3]):
        print(f"--- Image chunk {i} ---")
        print(f"Page: {chunk['page_no']}")
        print(f"Captions: {chunk['captions']}")
        print(f"Text: {chunk['text'][:500]}")
        print()

    with open("test_image_chunks.json", "w", encoding="utf-8") as f:
        json.dump(image_chunks, f, indent=2, ensure_ascii=False)
    print("Full image chunk list saved to: test_image_chunks.json")


if __name__ == "__main__":
    main()