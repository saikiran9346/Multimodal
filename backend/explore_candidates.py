from app.retrieval.vector_store import search_hybrid

CANDIDATES = [
    "What should I check regarding the direction of rotation before starting the pump?",
    "How should I clean the pump according to the maintenance section?",
    "What is the pump's enclosure class and sound pressure level?",
    "What does section 6 of this manual cover, and what are its subsections?",
    "What are the pump's standard mounting positions?",
    "How should the pump be disposed of at the end of its life?",
]

for question in CANDIDATES:
    print(f"\n{'='*70}\nQ: {question}\n{'='*70}")
    results = search_hybrid(question, top_k=5, exclude_images=False)
    for p in results:
        print(f"Page: {p.payload['page_no']} | Types: {p.payload.get('content_types')} | Headings: {p.payload['headings']}")
        print(f"  {p.payload['text'][:150]}")