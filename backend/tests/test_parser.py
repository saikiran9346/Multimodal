import glob
import os

from app.ingestion.parser import parse_pdf


def main():
    manuals_dir = os.path.join("..", "data", "sample_manuals")
    pdf_files = glob.glob(os.path.join(manuals_dir, "*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {manuals_dir}")
        return

    pdf_path = pdf_files[0]
    print(f"Parsing: {pdf_path}")

    markdown_text = parse_pdf(pdf_path)

    print(f"\nTotal characters extracted: {len(markdown_text)}")
    print("\n--- First 2000 characters ---\n")
    print(markdown_text[:2000])

    output_path = "test_output.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    print(f"\nFull output saved to: {output_path}")


if __name__ == "__main__":
    main()