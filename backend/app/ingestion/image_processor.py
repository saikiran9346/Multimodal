import base64
import io
import json
import os
import time

from groq import APIStatusError

from app.generation.llm import get_groq_client

RETRYABLE_STATUS_CODES = {429, 503}
MAX_RETRIES = 5
BASE_DELAY = 2


def _pil_to_data_url(image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _create_with_retry(client, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            return client.chat.completions.create(**kwargs)
        except APIStatusError as e:
            message = str(e)
            if e.status_code == 429 and ("per day" in message or "TPD" in message):
                print("\n  Hit Groq's daily token quota, not a transient error.")
                print("  Progress so far is saved. Wait for the quota to refresh,")
                print("  then rerun -- it resumes automatically.\n")
                raise
            if e.status_code not in RETRYABLE_STATUS_CODES or attempt == MAX_RETRIES - 1:
                raise
            delay = BASE_DELAY * (2 ** attempt)
            print(f"    Groq error {e.status_code}, retrying in {delay}s...")
            time.sleep(delay)


def describe_image(image, context: str = ""):
    """
    Classifies then describes an image via Groq vision. Returns None if
    the image is decorative/branding/navigational (logos, QR codes,
    marketing photography) -- carries no technical information and
    would just pollute the retrieval index. Returns the description
    string if the image is genuinely technical content.
    """
    client = get_groq_client()
    image_url = _pil_to_data_url(image)

    prompt = (
        "This image is from a technical pump manual. First classify it, "
        "then describe it if relevant.\n\n"
        "Line 1: output exactly one word -- RELEVANT or SKIP.\n"
        "- SKIP: company logos, QR codes, marketing or product "
        "photography, decorative images, or anything with no technical "
        "information content.\n"
        "- RELEVANT: technical diagrams, schematics, nameplates, wiring "
        "diagrams, mounting instructions, exploded views, dimensional "
        "drawings, or anything useful for understanding or operating "
        "the equipment.\n\n"
        "If RELEVANT: on the following lines, describe in detail what "
        "components are labeled, what the diagram shows, and any text, "
        "numbers, or codes visible.\n"
        "If SKIP: write nothing further."
    )
    if context:
        prompt += f"\n\nManual's own caption for this figure: {context}"

    try:
        response = _create_with_retry(
            client,
            model="qwen/qwen3.8-27b",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }],
            temperature=0.1,
            max_completion_tokens=1024,
        )
        result = response.choices[0].message.content.strip()
    except Exception as vision_err:
        print(f"    Vision classification skipped due to API limit/error: {str(vision_err)}")
        return None

    first_line, _, rest = result.partition("\n")
    if first_line.strip().upper().startswith("SKIP"):
        return None
    return rest.strip() if rest.strip() else result


def extract_image_chunks(document, file_path: str = None, chunks_path: str = "test_image_chunks.json",
                          progress_path: str = "test_image_progress.json") -> list[dict]:
    """
    Walks every PictureItem, classifies + describes each via Groq, and
    returns chunk-shaped dicts for RELEVANT images only. progress_path
    tracks every picture index ever processed (relevant or skipped) so
    reruns never waste a Groq call re-classifying an image already
    judged -- kept separate from chunks_path, which only holds chunks
    meant for embedding. Supports standalone image file paths.
    """
    chunks = []
    if os.path.exists(chunks_path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

    processed = set()
    if os.path.exists(progress_path):
        with open(progress_path, "r", encoding="utf-8") as f:
            processed = set(json.load(f))

    if processed:
        print(f"  Resuming: {len(processed)} image(s) already processed "
              f"({len(chunks)} kept as relevant)")

    pictures = getattr(document, "pictures", [])

    # If standalone image upload (not a PDF with embedded pictures)
    if not pictures and file_path and any(file_path.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]):
        if 0 not in processed:
            print(f"  Processing standalone image file '{os.path.basename(file_path)}'...")
            try:
                from PIL import Image
                img = Image.open(file_path)
                description = describe_image(img, context=os.path.basename(file_path))
                if description:
                    print("    -> RELEVANT, kept")
                    chunks.append({
                        "picture_index": 0,
                        "text": f"[Standalone Diagram/Image: {os.path.basename(file_path)}]\n{description}".strip(),
                        "raw_text": description,
                        "page_no": None,
                        "headings": [],
                        "captions": [],
                        "content_types": ["picture"],
                        "contains_table": False,
                    })
                    with open(chunks_path, "w", encoding="utf-8") as f:
                        json.dump(chunks, f, indent=2, ensure_ascii=False)
                else:
                    print("    -> SKIP (not technical content)")
            except Exception as img_err:
                print(f"    Failed to process standalone image: {str(img_err)}")
            processed.add(0)
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(sorted(processed), f)
        return chunks

    for i, picture in enumerate(pictures):
        if i in processed:
            continue

        print(f"  Processing image {i + 1}/{len(pictures)}...")
        image = picture.get_image(document)
        if image is None:
            print("    Skipped -- no pixel data")
            processed.add(i)
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(sorted(processed), f)
            continue

        page_no = picture.prov[0].page_no if picture.prov else None
        caption = picture.caption_text(doc=document) or ""
        description = describe_image(image, context=caption)

        if description is None:
            print("    -> SKIP (not technical content)")
        else:
            print("    -> RELEVANT, kept")
            chunks.append({
                "picture_index": i,
                "text": f"[Figure, page {page_no}] {caption}\n{description}".strip(),
                "raw_text": description,
                "page_no": page_no,
                "headings": [],
                "captions": [caption] if caption else [],
                "content_types": ["picture"],
                "contains_table": False,
            })
            with open(chunks_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)

        processed.add(i)
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(sorted(processed), f)

    return chunks