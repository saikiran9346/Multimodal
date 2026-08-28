import json

with open("tp_chunks.json", "r", encoding="utf-8") as f:
    text_chunks = json.load(f)

with open("tp_image_chunks.json", "r", encoding="utf-8") as f:
    image_chunks = json.load(f)

print(f"Text chunks: {len(text_chunks)}")
print(f"Image chunks: {len(image_chunks)}")

print("\n--- First 2 text chunks ---")
for c in text_chunks[:2]:
    print(f"Page: {c['page_no']} | Headings: {c['headings']}")
    print(f"  {c['text'][:200]}")
    print()

print("--- First 2 image chunks ---")
for c in image_chunks[:2]:
    print(f"Page: {c['page_no']} | Captions: {c['captions']}")
    print(f"  {c['text'][:200]}")
    print()
