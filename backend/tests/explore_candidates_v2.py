from app.retrieval.vector_store import search_hybrid

CANDIDATES = {
    "TABLE": [
        "What does item 19 represent on the motor nameplate?",
        "What is item 1 on the pump nameplate?",
        "What is the remedy if the pump runs but delivers no water, according to the fault-finding table?",
        "What is the maximum system pressure for a cast iron pump with shaft seal type AVBx?",
    ],
    "IMAGE": [
        "What does Fig. 3 show for the suction and discharge ports?",
        "What does Fig. 5 show about alternative connection positions?",
        "What does Fig. 6 show about terminal box positions?",
        "What does the motor nameplate diagram on page 14 show?",
    ],
    "MULTI_PAGE": [
        "What nameplate information is provided for both the pump and the motor?",
        "What are the pump's temperature and pressure operating limits?",
        "What mounting and connection position options does the pump have?",
    ],
    "SECTION_STRUCTURE": [
        "What does section 9 (Maintenance) cover, and what are its subsections?",
        "What does section 11 (Technical data) cover, and what are its subsections?",
    ],
    "EXACT_FACT": [
        "What is the maximum liquid temperature allowed for self-priming pumps?",
        "What non-return valve opening pressure is recommended for self-priming pumps?",
    ],
}

for category, questions in CANDIDATES.items():
    print(f"\n{'#'*70}\n{category}\n{'#'*70}")
    for question in questions:
        print(f"\n{'='*70}\nQ: {question}\n{'='*70}")
        results = search_hybrid(question, top_k=5, exclude_images=False)
        for p in results:
            print(f"Page: {p.payload['page_no']} | Types: {p.payload.get('content_types')} | Headings: {p.payload['headings']}")
            print(f"  {p.payload['text'][:150]}")