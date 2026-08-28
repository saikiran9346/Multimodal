import math


def recall_at_k(retrieved_pages: list[int], relevant_pages: list[int], k: int) -> float:
    """Of all pages that SHOULD have been found, what fraction were found in the top K?"""
    if not relevant_pages:
        return 0.0
    top_k = retrieved_pages[:k]
    found = set(top_k) & set(relevant_pages)
    return len(found) / len(set(relevant_pages))


def precision_at_k(retrieved_pages: list[int], relevant_pages: list[int], k: int) -> float:
    """Of the K results retrieved, what fraction were actually relevant?"""
    top_k = retrieved_pages[:k]
    if not top_k:
        return 0.0
    found = sum(1 for p in top_k if p in relevant_pages)
    return found / len(top_k)


def mrr(retrieved_pages: list[int], relevant_pages: list[int]) -> float:
    """
    1 / rank of the FIRST relevant result, or 0 if none found.
    Rewards an early hit, doesn't care how many relevant results exist.
    """
    for rank, page in enumerate(retrieved_pages, start=1):
        if page in relevant_pages:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_pages: list[int], relevant_pages: list[int], k: int) -> float:
    """
    Rewards relevant results more the earlier they appear (log discount),
    normalized against the best possible ordering so the result is
    always in [0, 1]. Each relevant page counts only once toward DCG,
    even if multiple chunks from that page appear in the results --
    otherwise finding the same right page twice could out-score finding
    two different right pages once each.
    """
    top_k = retrieved_pages[:k]
    relevant_set = set(relevant_pages)
    already_counted = set()

    dcg = 0.0
    for rank, page in enumerate(top_k, start=1):
        if page in relevant_set and page not in already_counted:
            dcg += 1.0 / math.log2(rank + 1)
            already_counted.add(page)

    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_query(retrieved_pages: list[int], relevant_pages: list[int], k: int = 5) -> dict:
    return {
        "recall_at_k": recall_at_k(retrieved_pages, relevant_pages, k),
        "precision_at_k": precision_at_k(retrieved_pages, relevant_pages, k),
        "mrr": mrr(retrieved_pages, relevant_pages),
        "ndcg_at_k": ndcg_at_k(retrieved_pages, relevant_pages, k),
    }


def average_metrics(per_query_metrics: list[dict]) -> dict:
    """Averages across all queries -- the numbers that go in a README table."""
    if not per_query_metrics:
        return {}
    keys = per_query_metrics[0].keys()
    return {k: sum(m[k] for m in per_query_metrics) / len(per_query_metrics) for k in keys}