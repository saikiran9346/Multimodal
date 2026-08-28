from fastembed import TextEmbedding

EMBED_MODEL_ID = "BAAI/bge-base-en-v1.5"

_model = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBED_MODEL_ID)
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    """
    Embeds document/chunk text for storage. Do not use this for
    query text -- see embed_query() below.
    """
    model = _get_model()
    prefixed = [f"passage: {t}" for t in texts]
    return [vec.tolist() for vec in model.embed(prefixed)]


def embed_query(text: str) -> list[float]:
    """
    Embeds a single search query, using the "query: " prefix -- the
    counterpart to embed_passages(). Always go through one of these
    two functions rather than calling the model directly elsewhere;
    using the wrong one silently hurts retrieval quality with no error.
    """
    model = _get_model()
    return list(model.embed([f"query: {text}"]))[0].tolist()