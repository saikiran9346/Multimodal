import os
import sys
import json
import types
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Shim deprecated vertexai import in ragas if missing in langchain_community
try:
    import langchain_community.chat_models.vertexai
except ModuleNotFoundError:
    m = types.ModuleType("langchain_community.chat_models.vertexai")
    m.ChatVertexAI = None
    sys.modules["langchain_community.chat_models.vertexai"] = m

load_dotenv()

from datasets import Dataset
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import FastEmbedEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

from app.api.routes.query import query_manual
from app.models.response import QueryRequest

QUESTIONS_PATH = os.path.abspath(os.path.join(backend_dir.parent, "data", "evaluation", "multi_pdf_questions.json"))
RESULTS_PATH = os.path.abspath(os.path.join(backend_dir.parent, "experiments", "results", "ragas_evaluation.json"))
TEST_RESULTS_PATH = os.path.join(Path(__file__).resolve().parent, "ragas_report.json")


def load_questions():
    if os.path.exists(QUESTIONS_PATH):
        with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {
            "query": "What is the maximum system pressure for a cast iron pump with shaft seal type AVBx?",
            "ground_truth": "For cast iron with shaft seal AVBx, max pressure is 10 bar from -20 to 40 C and 6 bar from 41 to 90 C.",
            "doc_name": "grundfos_cm_pump_manual.pdf"
        },
        {
            "query": "What is the minimum acceptable winding insulation resistance when measured at 500V DC megohmmeter?",
            "ground_truth": "Minimum acceptable insulation resistance is 100 Megohms at 25 degrees C.",
            "doc_name": "service_protocol.docx"
        },
        {
            "query": "What formula is used in Python to calculate Net Positive Suction Head Available (NPSHa)?",
            "ground_truth": "NPSHa = (P_suction - P_vapor) / (rho * g) + (V^2 / 2g)",
            "doc_name": "hydraulic_calculations.py"
        },
        {
            "query": "What electrical wiring diagram or motor connection layout is shown in fig9_wiring_diagram.png?",
            "ground_truth": "Terminal box connection interface with 8 terminal connection points arranged in two rows.",
            "doc_name": "fig9_wiring_diagram.png"
        }
    ]


def run_ragas_eval():
    print("=" * 70)
    print("        RAGAS MULTIMODAL RAG EVALUATION SUITE")
    print("=" * 70)

    questions_data = load_questions()
    sample_data = questions_data[:4] if len(questions_data) > 4 else questions_data

    print(f"\nProcessing {len(sample_data)} evaluation queries through Multimodal RAG pipeline...")

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for item in sample_data:
        q = item.get("query") or item.get("question")
        doc_name = item.get("doc_name")
        gt = item.get("ground_truth", "")

        req = QueryRequest(query=q, top_k=5, exclude_images=False, doc_name=doc_name)
        res = query_manual(req)

        ctx_list = [s.text for s in res.sources] if res.sources else ["No context retrieved."]
        
        questions.append(q)
        answers.append(res.answer)
        contexts.append(ctx_list)
        ground_truths.append(gt)
        print(f"  [OK] Processed query: '{q[:50]}...'")

    eval_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }

    dataset = Dataset.from_dict(eval_dict)

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    eval_llm = ChatOpenAI(
        model="qwen/qwen3.8-27b",
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.1,
        request_timeout=60.0
    )

    fastembed_model = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    eval_emb = LangchainEmbeddingsWrapper(fastembed_model)

    print("\nRunning RAGAS Metrics Evaluation (Faithfulness, Answer Relevancy, Context Precision)...")
    
    metrics = [faithfulness, answer_relevancy, context_precision]
    
    score_result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=eval_llm,
        embeddings=eval_emb
    )

    print("\n" + "=" * 70)
    print("                   RAGAS EVALUATION RESULTS")
    print("=" * 70)

    report = {
        "ragas_summary": {},
        "per_question_details": []
    }

    # Extract score metrics safely from RAGAS EvaluationResult object
    try:
        for metric_name, val in score_result.items():
            if isinstance(val, (int, float)):
                report["ragas_summary"][metric_name] = float(val)
                print(f"  • {metric_name:<25} : {val:.4f}")
    except Exception:
        pass

    for idx in range(len(questions)):
        detail = {
            "question": questions[idx],
            "answer": answers[idx],
            "ground_truth": ground_truths[idx]
        }
        report["per_question_details"].append(detail)

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(TEST_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved RAGAS report to:\n  • {RESULTS_PATH}\n  • {TEST_RESULTS_PATH}\n")
    print("=" * 70)


if __name__ == "__main__":
    run_ragas_eval()
