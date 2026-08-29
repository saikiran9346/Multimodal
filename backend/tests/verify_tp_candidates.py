from app.retrieval.vector_store import search_hybrid

CANDIDATES = [
    "What are the sound pressure levels and electrical data listed in the technical data section?",
    "What does the fault-finding table recommend if the pump is classified as contaminated?",
    "What does Fig. 5 illustrate regarding the use of washers for oval bolt holes during pump installation?",
    "What should be injected between the motor stool and shaft if the pump is drained for a long period of inactivity?",
    "What are the handling and delivery guidelines for TP and TPD pumps?",
    "What steps are required for startup, flushing, and priming the pipe system?",
    "What does section 5 (Installation) cover in the TP manual, and what are its subsections?",
    "What does section 8 (Maintenance and service) cover in the TP manual?",
]

for question in CANDIDATES:
    print(f"\n{'='*70}\nQ: {question}\n{'='*70}")
    for p in search_hybrid(question, top_k=5, exclude_images=False, doc_name="1_TP.pdf"):
        print(f"Page: {p.payload['page_no']} | Types: {p.payload.get('content_types')} | Headings: {p.payload['headings']}")
        print(f"  {p.payload['text'][:150]}")