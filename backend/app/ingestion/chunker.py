from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

EMBED_MODEL_ID = "BAAI/bge-base-en-v1.5"

_tokenizer = HuggingFaceTokenizer(
    tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
)


def chunk_document(document) -> list[dict]:
    """
    Uses Docling's structure-aware HybridChunker to split a parsed
    DoclingDocument into chunks, attaching page number, section
    headings, captions, and content types to each one.

    A chunk can legitimately contain more than one item type -- e.g.
    merge_peers combines a short intro paragraph with the table it
    introduces when both share a heading and fit the token budget. So
    content_types lists every distinct item type present in the chunk,
    and contains_table flags any chunk with real tabular data even if
    it's not the only thing in it.
    """
    chunker = HybridChunker(tokenizer=_tokenizer)
    chunks = []

    for chunk in chunker.chunk(dl_doc=document):
        doc_items = chunk.meta.doc_items or []
        first_item = doc_items[0] if doc_items else None
        page_no = first_item.prov[0].page_no if first_item and first_item.prov else None

        content_types = sorted({str(item.label) for item in doc_items})

        chunks.append({
            "text": chunker.contextualize(chunk),
            "raw_text": chunk.text,
            "page_no": page_no,
            "headings": chunk.meta.headings or [],
            "captions": chunk.meta.captions or [],
            "content_types": content_types,
            "contains_table": "table" in content_types,
        })

    return chunks