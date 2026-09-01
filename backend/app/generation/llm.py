from groq import Groq

from app.config import settings

_client = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key, timeout=30.0)
    return _client


def ask_groq(context: str, question: str) -> str:
    client = get_groq_client()

    prompt = (
        "You are a technical assistant answering questions about a manual. "
        "Use ONLY the context below to answer. If the answer isn't in the "
        "context, say so clearly instead of guessing.\n\n"
        f"--- CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
        f"Question: {question}"
    )

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        reasoning_effort="none",
        max_completion_tokens=1024,
    )

    return response.choices[0].message.content


def _format_doc_header(c: dict) -> str:
    doc_name = c.get("doc_name")
    page_no = c.get("page_no")
    headings = c.get("headings", [])
    first_heading = headings[0] if headings and len(headings) > 0 else None

    if doc_name and page_no is not None:
        return f"{doc_name} - Page {page_no}"
    elif doc_name and first_heading:
        return f"{doc_name} - {first_heading}"
    elif doc_name:
        return doc_name
    elif page_no is not None:
        return f"Page {page_no}"
    elif first_heading:
        return first_heading
    else:
        return "Source"


def generate_grounded_answer(question: str, chunks: list[dict]) -> dict:
    """
    Builds an answer from reranked chunks, each given a numbered
    citation tag referencing document filename and page number/heading.
    """
    client = get_groq_client()

    context_blocks = []
    for i, c in enumerate(chunks, start=1):
        doc_header = _format_doc_header(c)
        context_blocks.append(f"[{i}] ({doc_header})\n{c['text']}")

    context = "\n\n".join(context_blocks)

    prompt = (
        "You are an expert assistant that answers questions using ONLY the numbered evidence excerpts below. "
        "Rules:\n"
        "1. Use ONLY information present in the excerpts — never guess or add external knowledge.\n"
        "2. Cite each excerpt used with its number in square brackets like [1] right after the claim.\n"
        "3. If the question asks to LIST or ENUMERATE items (projects, skills, experiences, etc.), "
        "you MUST include EVERY single item found across ALL excerpts — do not skip or summarize. "
        "Output each item as a separate numbered entry.\n"
        "4. If the excerpts don't contain enough information, say so clearly.\n\n"
        f"{context}\n\n"
        f"Question: {question}"
    )

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        reasoning_effort="none",
        max_completion_tokens=2048,
    )

    sources = [
        {
            "index": i,
            "doc_name": c.get("doc_name"),
            "page_no": c.get("page_no"),
            "headings": c.get("headings", []),
            "content_types": c.get("content_types", ["text"]),
            "text": c.get("text"),
            "score": c.get("rerank_score", c.get("hybrid_score")),
        }
        for i, c in enumerate(chunks, start=1)
    ]

    return {"answer": response.choices[0].message.content, "sources": sources}