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

from app.generation.critique import agentic_rag_pipeline
from app.models.response import QueryRequest

QUESTIONS_PATH = os.path.abspath(os.path.join(backend_dir.parent, "data", "evaluation", "multi_pdf_questions.json"))
RESULTS_PATH = os.path.abspath(os.path.join(backend_dir.parent, "experiments", "results", "ragas_evaluation.json"))
TEST_RESULTS_PATH = os.path.join(Path(__file__).resolve().parent, "ragas_report.json")


def load_15_multi_doc_questions():
    questions = []
    
    # 1. Add questions from multi_pdf_questions.json (12 questions)
    if os.path.exists(QUESTIONS_PATH):
        with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
            pdf_q = json.load(f)
            for item in pdf_q[:12]:
                questions.append({
                    "query": item.get("question") or item.get("query"),
                    "ground_truth": item.get("notes", "Technical manual specifications."),
                    "doc_name": item.get("doc_name")
                })

    # 2. Add non-PDF format questions (3 questions: DOCX, Code, Standalone Image)
    extra_format_questions = [
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

    for eq in extra_format_questions:
        if len(questions) < 15:
            questions.append(eq)

    return questions[:15]


def run_ragas_eval():
    print("=" * 70, flush=True)
    print("    RAGAS AGENTIC RAG EVALUATION SUITE (15 QUESTIONS)", flush=True)
    print("    Self-Critique Agent: Approach B (Re-Retrieve + Re-Generate)", flush=True)
    print("=" * 70, flush=True)

    sample_data = load_15_multi_doc_questions()

    print(f"\nProcessing {len(sample_data)} evaluation queries via Self-Critique Agent pipeline...", flush=True)

    questions = []
    answers = []
    contexts = []
    ground_truths = []
    agent_stats = []

    # Check if cached results exist in TEST_RESULTS_PATH to save API generation time
    cached_details = None
    if os.path.exists(TEST_RESULTS_PATH) and "--force" not in sys.argv:
        try:
            with open(TEST_RESULTS_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if len(cached.get("per_question_details", [])) == len(sample_data):
                    cached_details = cached["per_question_details"]
        except Exception:
            cached_details = None

    if cached_details and all("contexts" in d for d in cached_details):
        print(f"Loading {len(cached_details)} pre-computed agent responses from cache...", flush=True)
        for d in cached_details:
            questions.append(d["question"])
            answers.append(d["answer"])
            contexts.append(d["contexts"])
            ground_truths.append(d["ground_truth"])
            agent_stats.append(d.get("agent", {"attempts": 1, "final_query": d["question"], "critique_log": []}))
    else:
        for idx, item in enumerate(sample_data, 1):
            q = item.get("query")
            doc_name = item.get("doc_name")
            gt = item.get("ground_truth", "")

            # Use the Self-Critique Agent pipeline instead of basic query_manual
            result = agentic_rag_pipeline(
                query=q,
                top_k=5,
                exclude_images=False,
                doc_name=doc_name,
                max_retries=2,
            )

            ctx_list = [c.get("text", "") for c in result["sources"]] if result["sources"] else ["No context retrieved."]
            
            questions.append(q)
            answers.append(result["answer"])
            contexts.append(ctx_list)
            ground_truths.append(gt)
            agent_stats.append({
                "attempts": result["attempts"],
                "final_query": result["final_query"],
                "critique_log": result["critique_log"],
            })
            attempts_str = f" [{result['attempts']} attempt(s)]" if result["attempts"] > 1 else ""
            print(f"  [{idx:02d}/15] Processed{attempts_str} ({doc_name}): '{q[:45]}...'", flush=True)

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
        model="openai/gpt-oss-120b",
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        temperature=0.0,
        request_timeout=60.0,
    )

    fastembed_model = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    eval_emb = LangchainEmbeddingsWrapper(fastembed_model)

    from ragas.run_config import RunConfig

    run_cfg = RunConfig(
        max_workers=2,
        timeout=120,
        max_retries=10,
        max_wait=30
    )

    print("\nRunning RAGAS Metrics Evaluation (Faithfulness, Answer Relevancy, Context Precision)...", flush=True)
    
    metrics = [faithfulness, answer_relevancy, context_precision]
    
    score_result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=eval_llm,
        embeddings=eval_emb,
        run_config=run_cfg,
        raise_exceptions=False,
    )

    print("\n" + "=" * 70, flush=True)
    print("         RAGAS AGENTIC EVALUATION RESULTS (15 MULTI-DOC QUESTIONS)", flush=True)
    print("=" * 70, flush=True)

    report = {
        "total_questions_evaluated": len(questions),
        "pipeline": "Self-Critique Agent (Approach B: Re-Retrieve + Re-Generate)",
        "ragas_summary": {},
        "agent_summary": {},
        "per_question_details": []
    }

    # Extract score metrics safely from RAGAS EvaluationResult object
    try:
        if hasattr(score_result, "to_pandas"):
            df = score_result.to_pandas()
            for col in ["faithfulness", "answer_relevancy", "context_precision"]:
                if col in df.columns:
                    val = float(df[col].dropna().mean())
                    report["ragas_summary"][col] = round(val, 4)
                    print(f"  • {col:<25} : {val:.4f}", flush=True)
        else:
            for k, v in dict(score_result).items():
                if isinstance(v, (int, float)):
                    report["ragas_summary"][k] = round(float(v), 4)
                    print(f"  • {k:<25} : {float(v):.4f}", flush=True)
    except Exception as ex:
        print(f"Notice during metric extraction: {ex}", flush=True)

    # Agent summary stats
    total_attempts = sum(s["attempts"] for s in agent_stats)
    multi_attempt_queries = sum(1 for s in agent_stats if s["attempts"] > 1)
    report["agent_summary"] = {
        "total_attempts": total_attempts,
        "avg_attempts_per_query": round(total_attempts / len(agent_stats), 2),
        "multi_attempt_queries": multi_attempt_queries,
        "single_attempt_queries": len(agent_stats) - multi_attempt_queries,
    }
    print(f"\n  Agent Stats:", flush=True)
    print(f"    Total attempts across {len(agent_stats)} queries: {total_attempts}", flush=True)
    print(f"    Avg attempts per query: {report['agent_summary']['avg_attempts_per_query']}", flush=True)
    print(f"    Queries needing re-retrieval: {multi_attempt_queries}/{len(agent_stats)}", flush=True)

    for idx in range(len(questions)):
        detail = {
            "question": questions[idx],
            "doc_name": sample_data[idx].get("doc_name"),
            "answer": answers[idx],
            "ground_truth": ground_truths[idx],
            "contexts": contexts[idx],
            "agent": agent_stats[idx],
        }
        report["per_question_details"].append(detail)

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    with open(TEST_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved RAGAS report to:\n  • {RESULTS_PATH}\n  • {TEST_RESULTS_PATH}\n", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    run_ragas_eval()

