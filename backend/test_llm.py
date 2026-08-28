import os
from app.generation.llm import ask_groq


def get_relevant_excerpt(full_text: str, marker: str, chars_before: int = 200, chars_after: int = 4000) -> str:
    """
    Finds the heading in the body (skipping the first match, which is the
    Table of Contents entry) and returns a slice around it. Stands in for
    what real chunk retrieval will do once Phase 3/4 are built.
    """
    first_index = full_text.find(marker)
    second_index = full_text.find(marker, first_index + 1)
    start_index = second_index if second_index != -1 else first_index

    if start_index == -1:
        raise ValueError(f"Marker '{marker}' not found in document")

    start = max(0, start_index - chars_before)
    end = min(len(full_text), start_index + chars_after)
    return full_text[start:end]


def main():
    output_path = "test_output.md"
    if not os.path.exists(output_path):
        print(f"Error: '{output_path}' not found. Please run 'python test_parser.py' first.")
        return

    with open(output_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    print(f"Full document: {len(markdown_text)} characters")

    excerpt = get_relevant_excerpt(markdown_text, "Mechanical installation")
    print(f"Excerpt sent to Groq: {len(excerpt)} characters")

    question = "What does this section of the manual cover, and what are its subsections?"
    print(f"Question: {question}\n")

    print("--- ANSWER ---\n")
    answer = ask_groq(context=excerpt, question=question)
    print(answer)


if __name__ == "__main__":
    main()