from pathlib import Path
from io import BytesIO

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
    PowerpointFormatOption,
    ExcelFormatOption,
    CsvFormatOption,
    HTMLFormatOption,
    MarkdownFormatOption,
    OdtFormatOption,
    OdsFormatOption,
    OdpFormatOption,
    LatexFormatOption,
    AsciiDocFormatOption,
    ImageFormatOption,
)
from docling.datamodel.pipeline_options import PdfPipelineOptions, PaginatedPipelineOptions
from docling.datamodel.base_models import InputFormat, DocumentStream

TEXT_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".c", ".cpp", ".java", ".go", ".rs", ".sh",
    ".json", ".yaml", ".yml", ".txt", ".log", ".xml"
}

_pdf_options = PdfPipelineOptions()
_pdf_options.generate_picture_images = True
_pdf_options.images_scale = 2.0

_docx_options = PaginatedPipelineOptions()
_docx_options.generate_page_images = True
_docx_options.images_scale = 2.0

_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=_pdf_options),
        InputFormat.DOCX: WordFormatOption(pipeline_options=_docx_options),
        InputFormat.PPTX: PowerpointFormatOption(),
        InputFormat.HTML: HTMLFormatOption(),
        InputFormat.MD: MarkdownFormatOption(),
        InputFormat.XLSX: ExcelFormatOption(),
        InputFormat.CSV: CsvFormatOption(),
        InputFormat.ODT: OdtFormatOption(),
        InputFormat.ODS: OdsFormatOption(),
        InputFormat.ODP: OdpFormatOption(),
        InputFormat.LATEX: LatexFormatOption(),
        InputFormat.ASCIIDOC: AsciiDocFormatOption(),
        InputFormat.IMAGE: ImageFormatOption(),
    }
)


def parse_document(file_path: str):
    """
    Parses technical documents across 25+ file formats:
    - Documents: PDF, DOCX, PPTX, XLSX, HTML, MD, CSV, ODT, ODS, ODP, TEX, ADOC
    - Code & Configs: PY, JS, TS, C, CPP, JAVA, GO, RS, SH, JSON, YAML, TXT, XML
    - Images: PNG, JPG, JPEG, TIFF, BMP
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in TEXT_CODE_EXTENSIONS:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        lang = ext.lstrip(".")
        md_text = f"# File: {path.name}\n\n```{lang}\n{content}\n```\n"
        stream = DocumentStream(name=f"{path.name}.md", stream=BytesIO(md_text.encode("utf-8")))
        result = _converter.convert(stream)
        return result.document
    else:
        result = _converter.convert(file_path)
        return result.document


def parse_pdf(pdf_path: str):
    """
    Backwards-compatible wrapper.
    """
    return parse_document(pdf_path)