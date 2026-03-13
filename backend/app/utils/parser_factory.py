from app.utils.epub_parser import EpubParser
from app.utils.pdf_parser import PdfParser


def get_parser(filepath: str):
    lowered = filepath.lower()
    if lowered.endswith(".epub"):
        return EpubParser(filepath)
    if lowered.endswith(".pdf"):
        return PdfParser(filepath)
    raise ValueError(f"Unsupported file type: {filepath}")
