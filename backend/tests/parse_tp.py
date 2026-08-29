import os
import json
from docling_core.types.doc.document import DoclingDocument
from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk_document
from app.ingestion.image_processor import extract_image_chunks

PDF_PATH = os.path.join("..", "data", "sample_manuals", "1_TP.pdf")
CACHE_DOC_PATH = "tp_parsed_doc.json"
CHUNKS_PATH = "tp_chunks.json"
IMAGE_CHUNKS_PATH = "tp_image_chunks.json"
IMAGE_PROGRESS_PATH = "tp_image_progress.json"


def main():
    if os.path.exists(CACHE_DOC_PATH):
        print(f"Loading cached parsed document from {CACHE_DOC_PATH}...")
        document = DoclingDocument.load_from_json(CACHE_DOC_PATH)
    else:
        print(f"Parsing {PDF_PATH} with Docling...")
        document = parse_pdf(PDF_PATH)
        document.save_as_json(CACHE_DOC_PATH)
        print(f"Saved parsed document to {CACHE_DOC_PATH}")

    # Chunk text & tables
    if os.path.exists(CHUNKS_PATH):
        print(f"Loading cached chunks from {CHUNKS_PATH}...")
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            text_chunks = json.load(f)
    else:
        print("Chunking document...")
        text_chunks = chunk_document(document)
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(text_chunks, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(text_chunks)} text chunks to {CHUNKS_PATH}")

    # Extract image chunks
    print("Extracting image/diagram chunks...")
    image_chunks = extract_image_chunks(
        document,
        chunks_path=IMAGE_CHUNKS_PATH,
        progress_path=IMAGE_PROGRESS_PATH,
    )
    print(f"Total {len(image_chunks)} relevant image chunks extracted.")

    print(f"\n1_TP.pdf processing complete: {len(text_chunks)} text chunks, {len(image_chunks)} image chunks.")


if __name__ == "__main__":
    main()
