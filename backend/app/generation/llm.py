from groq import Groq

from app.config import settings

_client = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
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
        model="qwen/qwen3.6-27b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        reasoning_effort="none",
        max_completion_tokens=1024,
    )

    return response.choices[0].message.content


def generate_grounded_answer(question: str, chunks: list[dict]) -> dict:
    """
    Builds an answer from reranked chunks, each given a numbered
    citation tag referencing document filename and page number.
    """
    client = get_groq_client()

    context_blocks = []
    for i, c in enumerate(chunks, start=1):
        doc_header = f"{c['doc_name']} - Page {c['page_no']}" if c.get("doc_name") else f"Page {c['page_no']}"
        context_blocks.append(f"[{i}] ({doc_header})\n{c['text']}")

    context = "\n\n".join(context_blocks)

    prompt = (
        "You are a technical assistant answering questions about technical documents/manuals, "
        "using only the numbered evidence excerpts below. Every claim in "
        "your answer must be traceable to one of these excerpts -- cite "
        "the excerpt number in square brackets, like [1], right after the "
        "claim it supports. If the excerpts don't contain enough "
        "information to answer, say so clearly instead of guessing.\n\n"
        f"{context}\n\n"
        f"Question: {question}"
    )

    response = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        reasoning_effort="none",
        max_completion_tokens=1024,
    )

    sources = [
        {
            "index": i,
            "doc_name": c.get("doc_name"),
            "page_no": c["page_no"],
            "headings": c["headings"],
            "content_types": c.get("content_types", ["text"]),
            "text": c.get("text"),
            "score": c.get("rerank_score", c.get("hybrid_score")),
        }
        for i, c in enumerate(chunks, start=1)
    ]

    return {"answer": response.choices[0].message.content, "sources": sources}