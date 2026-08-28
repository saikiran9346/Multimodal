import json
import re

NEGATION_PATTERNS = [
    r"\bdoes not depict\b",
    r"\bis not a technical\b",
    r"\bnot a technical\b",
    r"\bnot depict a technical\b",
]


def looks_self_contradicting(text: str) -> bool:
    # Check only the first ~300 chars -- that's consistently where
    # these descriptions put an "actually, this isn't..." hedge.
    head = text[:300].lower()
    return any(re.search(p, head) for p in NEGATION_PATTERNS)


with open("test_image_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

kept, removed = [], []
for c in chunks:
    has_caption = bool(c.get("captions"))
    contradicts = looks_self_contradicting(c["text"])

    if not has_caption and contradicts:
        removed.append(c)
    else:
        kept.append(c)

print(f"Keeping {len(kept)}, removing {len(removed)} (self-contradicting with no manual caption backing them):")
for c in removed:
    print(f"  picture_index {c['picture_index']} (page {c['page_no']}): {c['text'][:120]}")

with open("test_image_chunks.json", "w", encoding="utf-8") as f:
    json.dump(kept, f, indent=2, ensure_ascii=False)

print(f"\n{len(kept)} image descriptions remain.")