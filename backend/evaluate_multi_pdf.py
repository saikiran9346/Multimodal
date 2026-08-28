import os
import json
import math
from pathlib import Path

from app.retrieval.vector_store import search_dense, search_hybrid, detect_document_from_query
from app.retrieval.reranker import rerank

QUESTIONS_PATH = os.path.join("..", "data", "evaluation", "multi_pdf_questions.json")
RESULTS_PATH = os.path.join("..", "experiments", "results", "multi_pdf_evaluation.json")


def load_questions():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def recall_at_k(retrieved, relevant, k=5):
    top_k = retrieved[:k]
    found = set(top_k) & set(relevant)
    return len(found) / len(set(relevant)) if relevant else 0.0


def precision_at_k(retrieved, relevant, k=5):
    top_k = retrieved[:k]
    found = set(top_k) & set(relevant)
    return len(found) / k if k > 0 else 0.0


def mean_reciprocal_rank(retrieved, relevant):
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved, relevant, k=5):
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


def evaluate_arm(label, retrieve_fn, questions):
    print(f"\n{'='*75}")
    print(f"EVALUATING ARM: {label}")
    print(f"{'='*75}")

    per_question_results = []
    recalls, precisions, mrrs, ndcgs = [], [], [], []

    for q in questions:
        expected = [(q["doc_name"], p) for p in q["relevant_pages"]]
        retrieved = retrieve_fn(q["question"])
        
        r = recall_at_k(retrieved, expected, k=5)
        p = precision_at_k(retrieved, expected, k=5)
        m = mean_reciprocal_rank(retrieved, expected)
        n = ndcg_at_k(retrieved, expected, k=5)

        recalls.append(r)
        precisions.append(p)
        mrrs.append(m)
        ndcgs.append(n)

        # Format retrieved for clear terminal display
        retrieved_display = [f"({doc.split('_')[0]}.. p.{page})" for doc, page in retrieved[:5]]
        expected_display = [f"({doc.split('_')[0]}.. p.{page})" for doc, page in expected]

        print(f"[{q['id']}] {q['question'][:58]:<58}")
        print(f"     Target: {expected_display} | Retrieved: {retrieved_display}")
        print(f"     Recall@5={r:.2f}  Precision@5={p:.2f}  MRR={m:.2f}  NDCG@5={n:.2f}")

        per_question_results.append({
            "id": q["id"],
            "category": q.get("category", "GENERAL"),
            "question": q["question"],
            "expected": expected,
            "retrieved": retrieved[:5],
            "recall@5": r,
            "precision@5": p,
            "mrr": m,
            "ndcg@5": n,
        })

    avg_metrics = {
        "recall@5": round(sum(recalls) / len(recalls), 4),
        "precision@5": round(sum(precisions) / len(precisions), 4),
        "mrr": round(sum(mrrs) / len(mrrs), 4),
        "ndcg@5": round(sum(ndcgs) / len(ndcgs), 4),
    }

    print(f"\n--- {label} SUMMARY ---")
    print(f"Recall@5:    {avg_metrics['recall@5']:.4f}")
    print(f"Precision@5: {avg_metrics['precision@5']:.4f}")
    print(f"MRR:         {avg_metrics['mrr']:.4f}")
    print(f"NDCG@5:      {avg_metrics['ndcg@5']:.4f}")

    return {
        "arm": label,
        "summary": avg_metrics,
        "per_question": per_question_results,
    }


def dense_retrieve(query):
    doc_filter = detect_document_from_query(query)
    points = search_dense(query, top_k=5, exclude_images=True, doc_name=doc_filter)
    return [(p.payload.get("doc_name"), p.payload["page_no"]) for p in points]


def hybrid_retrieve(query):
    doc_filter = detect_document_from_query(query)
    points = search_hybrid(query, top_k=5, exclude_images=True, doc_name=doc_filter)
    return [(p.payload.get("doc_name"), p.payload["page_no"]) for p in points]


def hybrid_reranked_retrieve(query):
    doc_filter = detect_document_from_query(query)
    points = search_hybrid(query, top_k=15, exclude_images=True, doc_name=doc_filter)
    dicts = [dict(p.payload, hybrid_score=p.score) for p in points]
    reranked = rerank(query, dicts, top_k=5)
    return [(c.get("doc_name"), c["page_no"]) for c in reranked]


def multimodal_retrieve(query):
    doc_filter = detect_document_from_query(query)
    points = search_hybrid(query, top_k=15, exclude_images=False, doc_name=doc_filter)
    dicts = [dict(p.payload, hybrid_score=p.score) for p in points]
    reranked = rerank(query, dicts, top_k=5)
    return [(c.get("doc_name"), c["page_no"]) for c in reranked]


def main():
    questions = load_questions()
    print(f"Loaded {len(questions)} Multi-PDF benchmark evaluation questions.")

    results = {}
    results["baseline_dense"] = evaluate_arm("1. Baseline Dense (BGE)", dense_retrieve, questions)
    results["hybrid_rrf"] = evaluate_arm("2. Hybrid Search (Dense + BM25 RRF)", hybrid_retrieve, questions)
    results["hybrid_reranked"] = evaluate_arm("3. Hybrid + Cross-Encoder Reranker", hybrid_reranked_retrieve, questions)
    results["multimodal_final"] = evaluate_arm("4. Multimodal (Text + Tables + Vision Chunks)", multimodal_retrieve, questions)

    # Save comprehensive results
    Path(os.path.dirname(RESULTS_PATH)).mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved Multi-PDF benchmark results to {RESULTS_PATH}")

    # Print Final Comparison Table
    print("\n" + "=" * 75)
    print("FINAL MULTI-PDF BENCHMARK COMPARISON TABLE (25 Questions, 422 Chunks)")
    print("=" * 75)
    print(f"{'Pipeline Architecture':<38} | {'Recall@5':<9} | {'Precision@5':<12} | {'MRR':<8} | {'NDCG@5':<8}")
    print("-" * 80)
    for key, data in results.items():
        s = data["summary"]
        print(f"{data['arm']:<38} | {s['recall@5']:<9.4f} | {s['precision@5']:<12.4f} | {s['mrr']:<8.4f} | {s['ndcg@5']:<8.4f}")
    print("=" * 75)


if __name__ == "__main__":
    main()
