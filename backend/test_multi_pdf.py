from app.retrieval.vector_store import search_hybrid


def print_results(label, results):
    print(f"\n{'='*70}")
    print(f"{label}")
    print(f"{'='*70}")
    for i, p in enumerate(results, start=1):
        doc = p.payload.get("doc_name", "UNKNOWN")
        page = p.payload.get("page_no")
        types = p.payload.get("content_types", ["text"])
        headings = p.payload.get("headings", [])
        snippet = p.payload.get("text", "")[:180].replace("\n", " ")
        print(f"[{i}] Doc: {doc} | Page {page} | Types: {types} | Score: {p.score:.4f}")
        if headings:
            print(f"    Headings: {' > '.join(headings)}")
        print(f"    Text: {snippet}...")


def main():
    print("=" * 70)
    print("MULTI-DOCUMENT RETRIEVAL VERIFICATION (Workflow A)")
    print("=" * 70)

    # 1. Grundfos CM-specific query -- should retrieve grundfos_cm_pump_manual.pdf
    print_results(
        "1. Grundfos CM Query: 'What is shaft seal type AQQx rated for?'",
        search_hybrid("What is shaft seal type AQQx rated for?", top_k=5),
    )

    # 2. TP-specific query -- should retrieve 1_TP.pdf
    print_results(
        "2. TP Manual Query: 'How should TP and TPD pumps be lifted according to Fig. 1 and Fig. 2?'",
        search_hybrid("How should TP and TPD pumps be lifted according to Fig. 1 and Fig. 2?", top_k=5),
    )

    # 3. Filtered to Grundfos CM only -- even with both indexed, MUST return ONLY Grundfos
    print_results(
        "3. Scoped Search (Grundfos Only): 'maintenance'",
        search_hybrid("maintenance", top_k=5, doc_name="grundfos_cm_pump_manual.pdf"),
    )

    # 4. Filtered to TP only -- MUST return ONLY 1_TP.pdf
    print_results(
        "4. Scoped Search (TP Only): 'maintenance and service'",
        search_hybrid("maintenance and service", top_k=5, doc_name="1_TP.pdf"),
    )

    print("\n" + "=" * 70)
    print("Multi-PDF Retrieval Verification Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
