from fastembed.rerank.cross_encoder import TextCrossEncoder

RERANKER_MODEL_ID = "BAAI/bge-reranker-base"

_reranker = None


def _get_reranker() -> TextCrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = TextCrossEncoder(model_name=RERANKER_MODEL_ID)
    return _reranker


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-scores retrieved chunks against the query using a cross-encoder.
    candidates must be plain dicts with a "text" key -- keeps this
    module independent of Qdrant's result types.
    """
    if not candidates:
        return []

    reranker = _get_reranker()
    texts = [c["text"] for c in candidates]
    scores = list(reranker.rerank(query, texts))

    scored = list(zip(scores, candidates))
    scored.sort(key=lambda x: -x[0])

    reranked = []
    for score, candidate in scored[:top_k]:
        result = dict(candidate)
        result["rerank_score"] = float(score)
        reranked.append(result)

    return reranked