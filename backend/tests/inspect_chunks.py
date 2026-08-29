import json

with open("test_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

type_counts = {}
for chunk in chunks:
    for ct in chunk["content_types"]:
        type_counts[ct] = type_counts.get(ct, 0) + 1

print("Content type breakdown (a chunk can count toward more than one type):")
for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {ct}: {count}")

table_chunks = [c for c in chunks if c["contains_table"]]
print(f"\nFound {len(table_chunks)} chunks containing table data")

target_chunks = [c for c in chunks if "Capacitor size and voltage" in c["text"]]
print(f"\nFound {len(target_chunks)} chunk(s) containing 'Capacitor size and voltage'")
for c in target_chunks:
    print(json.dumps(c, indent=2))