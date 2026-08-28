import json
import os
from typing import Callable

from app.evaluation.dataset import load_questions
from app.evaluation.metrics import evaluate_query, average_metrics


def run_experiment(name: str, retrieve_fn: Callable[[str], list], k: int,
                    questions_path: str, results_dir: str) -> dict:
    """
    Runs every question in the eval set through retrieve_fn, scores the
    result against ground truth, and saves per-question + averaged
    metrics to results_dir/<name>.json. retrieve_fn takes a question
    string and returns an ordered list of page numbers.
    """
    questions = load_questions(questions_path)

    per_question = []
    for q in questions:
        retrieved_pages = retrieve_fn(q["question"])
        metrics = evaluate_query(retrieved_pages, q["relevant_pages"], k=k)
        per_question.append({
            "id": q["id"],
            "question": q["question"],
            "retrieved_pages": retrieved_pages,
            **metrics,
        })

    metrics_only = [
        {key: val for key, val in pq.items() if key not in ("id", "question", "retrieved_pages")}
        for pq in per_question
    ]
    averages = average_metrics(metrics_only)

    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"{name}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"experiment": name, "per_question": per_question, "averages": averages}, f, indent=2, ensure_ascii=False)

    print(f"=== {name} ===")
    for key, val in averages.items():
        print(f"  {key}: {val:.3f}")
    print(f"Saved to {out_path}")

    return averages