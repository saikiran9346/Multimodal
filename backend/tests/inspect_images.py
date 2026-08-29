import json

with open("test_image_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"{len(chunks)} image descriptions saved so far\n")
for c in chunks[:3]:
    print(f"--- Picture index {c['picture_index']} (page {c['page_no']}) ---")
    print(f"Caption: {c['captions']}")
    print(f"Description: {c['text'][:500]}")
    print()