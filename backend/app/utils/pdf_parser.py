class PdfParser:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def extract(self) -> list[dict]:
        # TODO: implement using pdfplumber library
        raise NotImplementedError("PDF support coming soon")
