import json
import urllib.request

TEST_SUITE = [
    {
        "category": "1. Exact Part Code (BM25 Keyword Search)",
        "query": "What is shaft seal type AQQx rated for?",
        "expected_page": 11,
    },
    {
        "category": "2. Table / Specification Search",
        "query": "What is the remedy if the pump runs but delivers no water, according to the fault-finding table?",
        "expected_page": 13,
    },
    {
        "category": "3. Multimodal / Technical Diagram Search",
        "query": "What are the pump's standard mounting positions?",
        "expected_page": 4,
    },
    {
        "category": "4. Technical Procedure & Safety Search",
        "query": "What should I check regarding the direction of rotation before starting the pump?",
        "expected_page": 9,
    },
]


def test_query(item):
    print("=" * 70)
    print(f"Category: {item['category']}")
    print(f"Query:    '{item['query']}'")
    print(f"Expected Page: {item['expected_page']}")
    print("-" * 70)

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/query",
        data=json.dumps({"query": item["query"], "top_k": 3}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req) as response:
        assert response.status == 200, f"Expected status 200, got {response.status}"
        data = json.loads(response.read().decode("utf-8"))

    print("\n--- Grounded Answer ---")
    print(data["answer"])

    print("\n--- Retrieved Sources ---")
    retrieved_pages = []
    for s in data["sources"]:
        page = s.get("page_no")
        retrieved_pages.append(page)
        types = s.get("content_types", [])
        score = s.get("score")
        score_str = f"{score:.4f}" if score is not None else "N/A"
        print(f"  [{s['index']}] Page {page} | Types: {types} | Score: {score_str}")

    is_hit = item["expected_page"] in retrieved_pages
    first_rank_match = retrieved_pages[0] == item["expected_page"] if retrieved_pages else False
    
    print(f"\nTarget Page Retrieved: {'YES' if is_hit else 'NO'}")
    print(f"Rank #1 Accuracy:     {'PERFECT MATCH' if first_rank_match else 'MATCHED IN TOP 3' if is_hit else 'MISSED'}")
    print("=" * 70 + "\n")
    return is_hit


def main():
    print("\n" + "#" * 70)
    print("TESTING MULTIMODAL RAG BACKEND ACROSS ALL QUERY MODALITIES")
    print("#" * 70 + "\n")

    hits = 0
    for item in TEST_SUITE:
        if test_query(item):
            hits += 1

    print("#" * 70)
    print(f"Summary: {hits}/{len(TEST_SUITE)} queries successfully retrieved expected ground-truth pages!")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    main()
