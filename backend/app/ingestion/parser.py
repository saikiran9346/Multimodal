from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat


def parse_pdf(pdf_path: str):
    """
    Parses a PDF with Docling and returns the DoclingDocument object.
    generate_picture_images=True is required for Phase 8 -- without it,
    every PictureItem.get_image() call returns None, since Docling
    doesn't keep pixel data by default. images_scale=2.0 gives higher-
    resolution crops so the vision model can actually read small labels
    and text inside diagrams.
    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    pipeline_options.images_scale = 2.0

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )
    result = converter.convert(pdf_path)
    return result.document