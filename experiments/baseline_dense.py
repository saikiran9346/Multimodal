import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.retrieval.vector_store import search_dense
from app.evaluation.runner import run_experiment


def retrieve(question: str) -> list:
    results = search_dense(question, top_k=5, exclude_images=True)
    return [p.payload["page_no"] for p in results]


if __name__ == "__main__":
    run_experiment(
        "baseline_dense",
        retrieve,
        k=5,
        questions_path=str(PROJECT_ROOT / "data" / "evaluation" / "questions.json"),
        results_dir=str(PROJECT_ROOT / "experiments" / "results"),
    )