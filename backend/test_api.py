import sys
import json
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    print("Testing GET /api/health ...")
    response = client.get("/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("[PASS] Health check PASSED\n")


def test_query():
    print("Testing POST /api/query ...")
    payload = {
        "query": "What is shaft seal type AQQx rated for?",
        "top_k": 5,
        "exclude_images": False,
    }
    response = client.post("/api/query", json=payload)
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    
    print("\n--- Grounded Answer ---")
    print(data["answer"])
    
    print(f"\n--- Sources ({len(data['sources'])}) ---")
    for s in data["sources"]:
        score_str = f"{s['score']:.4f}" if s.get('score') is not None else "N/A"
        print(f"[{s['index']}] Page {s['page_no']} | Types: {s['content_types']} | Score: {score_str}")
        print(f"    Headings: {s['headings']}")
        print(f"    Text: {s['text'][:120]}...\n")
        
    assert "answer" in data and len(data["answer"]) > 0
    assert len(data["sources"]) > 0
    print("[PASS] Query endpoint PASSED\n")


def main():
    print("=" * 60)
    print("Running FastAPI Endpoint Verification Tests")
    print("=" * 60 + "\n")
    
    test_health()
    test_query()
    
    print("=" * 60)
    print("All Phase 11 FastAPI Endpoints Verified Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
