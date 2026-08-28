import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.retrieval.vector_store import search_hybrid
from app.retrieval.reranker import rerank
from app.evaluation.runner import run_experiment


def retrieve(question: str) -> list:
    hybrid_results = search_hybrid(question, top_k=10, exclude_images=False)
    hybrid_dicts = [dict(p.payload, hybrid_score=p.score) for p in hybrid_results]
    reranked = rerank(question, hybrid_dicts, top_k=5)
    return [c["page_no"] for c in reranked]


if __name__ == "__main__":
    run_experiment(
        "multimodal",
        retrieve,
        k=5,
        questions_path=str(PROJECT_ROOT / "data" / "evaluation" / "questions.json"),
        results_dir=str(PROJECT_ROOT / "experiments" / "results"),
    )