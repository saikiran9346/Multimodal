import math

from app.retrieval.vector_store import search_dense, search_hybrid
from app.retrieval.reranker import rerank

# Reused from the already-verified single-doc eval set -- real, confirmed
# pages, now just tagged with which document. Not new ground truth.
CONFIRMED_QUESTIONS = [
    {
        "question": "What is shaft seal type AQQx rated for?",
        "relevant": [("grundfos_cm_pump_manual.pdf", 11)],
    },
    {
        "question": "What should I check before installing the pump, according to section 6?",
        "relevant": [("grundfos_cm_pump_manual.pdf", 4)],
    },
    {
        "question": "How should the pump be disposed of at the end of its life?",
        "relevant": [("grundfos_cm_pump_manual.pdf", 13)],
    },
]

# Not scored -- ground truth for 1_TP.pdf hasn't been verified against real
# content the way every other question in this project has been. Printed
# raw so you can judge relevance yourself.
UNVERIFIED_TP_CANDIDATES = [
    "How should TP and TPD pumps be lifted according to Fig. 1 and Fig. 2?",
]


def to_pages(results):
    return [(p.payload.get("doc_name"), p.payload["page_no"]) for p in results]


def recall_at_k(retrieved, relevant, k):
    top_k = retrieved[:k]
    found = set(top_k) & set(relevant)
    return len(found) / len(set(relevant)) if relevant else 0.0


def mrr(retrieved, relevant):
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved, relevant, k):
    top_k = retrieved[:k]
    relevant_set = set(relevant)
    counted = set()
    dcg = 0.0
    for rank, item in enumerate(top_k, start=1):
        if item in relevant_set and item not in counted:
            dcg += 1.0 / math.log2(rank + 1)
            counted.add(item)
    ideal_hits = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


def run_arm(label, retrieve_fn):
    print(f"\n{'='*70}\n{label}\n{'='*70}")
    all_recall, all_mrr, all_ndcg = [], [], []
    for q in CONFIRMED_QUESTIONS:
        retrieved = retrieve_fn(q["question"])
        r = recall_at_k(retrieved, q["relevant"], k=5)
        m = mrr(retrieved, q["relevant"])
        n = ndcg_at_k(retrieved, q["relevant"], k=5)
        all_recall.append(r)
        all_mrr.append(m)
        all_ndcg.append(n)
        print(f"  [{q['question'][:50]}...] Recall={r:.2f} MRR={m:.2f} NDCG={n:.2f}")
        print(f"    Retrieved: {retrieved}")

    n = len(all_recall)
    print(f"  AVG: Recall={sum(all_recall)/n:.3f} MRR={sum(all_mrr)/n:.3f} NDCG={sum(all_ndcg)/n:.3f}")


def dense_retrieve(question):
    return to_pages(search_dense(question, top_k=5, exclude_images=True))


def hybrid_retrieve(question):
    return to_pages(search_hybrid(question, top_k=5, exclude_images=True))


def hybrid_reranked_retrieve(question):
    results = search_hybrid(question, top_k=10, exclude_images=True)
    dicts = [dict(p.payload, hybrid_score=p.score) for p in results]
    reranked = rerank(question, dicts, top_k=5)
    return [(c.get("doc_name"), c["page_no"]) for c in reranked]


def multimodal_retrieve(question):
    results = search_hybrid(question, top_k=10, exclude_images=False)
    dicts = [dict(p.payload, hybrid_score=p.score) for p in results]
    reranked = rerank(question, dicts, top_k=5)
    return [(c.get("doc_name"), c["page_no"]) for c in reranked]


def main():
    print("Running against the CURRENT live collection (both documents indexed).\n")

    run_arm("Dense only", dense_retrieve)
    run_arm("Hybrid RRF", hybrid_retrieve)
    run_arm("Hybrid + Reranked", hybrid_reranked_retrieve)
    run_arm("Multimodal", multimodal_retrieve)

    print(f"\n{'='*70}\nUnverified TP.pdf candidate (raw results, no scoring)\n{'='*70}")
    for question in UNVERIFIED_TP_CANDIDATES:
        print(f"\nQ: {question}")
        for p in search_hybrid(question, top_k=5, exclude_images=False):
            print(f"  doc: {p.payload.get('doc_name')} | page: {p.payload['page_no']}")
            print(f"    {p.payload['text'][:150]}")


if __name__ == "__main__":
    main()