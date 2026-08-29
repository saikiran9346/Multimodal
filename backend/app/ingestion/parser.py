from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
    PowerpointFormatOption,
    ExcelFormatOption,
    CsvFormatOption,
    HTMLFormatOption,
    MarkdownFormatOption,
)
from docling.datamodel.pipeline_options import PdfPipelineOptions, PaginatedPipelineOptions
from docling.datamodel.base_models import InputFormat


def parse_document(file_path: str):
    """
    Parses technical documents (PDF, DOCX, PPTX, XLSX, HTML, MD, CSV) with Docling
    and returns the parsed DoclingDocument object.
    
    Format configurations:
    - PDF: PdfPipelineOptions(generate_picture_images=True, images_scale=2.0)
    - DOCX: PaginatedPipelineOptions(generate_page_images=True, images_scale=2.0)
    - PPTX: PowerpointFormatOption (defaults)
    - HTML: HTMLFormatOption (defaults)
    - MD: MarkdownFormatOption (defaults)
    - XLSX: ExcelFormatOption (defaults)
    - CSV: CsvFormatOption (defaults)
    """
    pdf_options = PdfPipelineOptions()
    pdf_options.generate_picture_images = True
    pdf_options.images_scale = 2.0

    docx_options = PaginatedPipelineOptions()
    docx_options.generate_page_images = True
    docx_options.images_scale = 2.0

    format_options = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options),
        InputFormat.DOCX: WordFormatOption(pipeline_options=docx_options),
        InputFormat.PPTX: PowerpointFormatOption(),
        InputFormat.HTML: HTMLFormatOption(),
        InputFormat.MD: MarkdownFormatOption(),
        InputFormat.XLSX: ExcelFormatOption(),
        InputFormat.CSV: CsvFormatOption(),
    }

    converter = DocumentConverter(format_options=format_options)
    result = converter.convert(file_path)
    return result.document


def parse_pdf(pdf_path: str):
    """
    Backwards-compatible wrapper for PDF parsing.
    """
    return parse_document(pdf_path)