from app.evaluation.dataset import load_questions
from app.evaluation.metrics import evaluate_query, average_metrics
from app.retrieval.vector_store import search_hybrid
from app.retrieval.reranker import rerank
def main():
    questions = load_questions()
    print(f"Loaded {len(questions)} questions\n")

    all_metrics = []
    for q in questions:
        hybrid_results = search_hybrid(q["question"], top_k=10)
        hybrid_dicts = [dict(p.payload, hybrid_score=p.score) for p in hybrid_results]
        reranked = rerank(q["question"], hybrid_dicts, top_k=5)

        retrieved_pages = [c["page_no"] for c in reranked]
        metrics = evaluate_query(retrieved_pages, q["relevant_pages"], k=5)
        all_metrics.append(metrics)

        print(f"[{q['id']}] {q['question']}")
        print(f"  Expected pages: {q['relevant_pages']}")
        print(f"  Retrieved pages (top 5): {retrieved_pages}")
        print(f"  Recall@5={metrics['recall_at_k']:.2f}  Precision@5={metrics['precision_at_k']:.2f}  "
              f"MRR={metrics['mrr']:.2f}  NDCG@5={metrics['ndcg_at_k']:.2f}")
        print()

    avg = average_metrics(all_metrics)
    print("=== Averages across all questions ===")
    for k, v in avg.items():
        print(f"  {k}: {v:.3f}")


if __name__ == "__main__":
    main()