import json

from docling_core.types.doc.document import DoclingDocument

CACHE_PATH = "test_parsed_doc.json"

with open("test_image_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

target = next(c for c in chunks if c["page_no"] == 7 and any("Wiring diagram" in cap for cap in c["captions"]))

print("Full description text:\n")
print(target["text"])
print(f"\npicture_index: {target['picture_index']}")

document = DoclingDocument.load_from_json(CACHE_PATH)
picture = document.pictures[target["picture_index"]]
image = picture.get_image(document)

if image is None:
    print("\nNo pixel data available for this picture.")
else:
    output_path = "fig9_wiring_diagram.png"
    image.save(output_path)
    print(f"\nSaved image to: {output_path}")
    print("Open this file yourself and look at it -- that's the actual ground truth.")