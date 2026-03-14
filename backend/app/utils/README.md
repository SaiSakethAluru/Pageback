# `utils/`

This folder contains utility helpers used by backend services.

## Contents

- `__init__.py`: package marker.
- `epub_parser.py`: EPUB extraction using `ebooklib` and `BeautifulSoup`.
- `pdf_parser.py`: PDF parser stub for future support.
- `parser_factory.py`: selects a parser based on file extension.
- `token_counter.py`: token counting with cached `tiktoken` encoders.

## Notes

- `parser_factory.py` is the entry point used by the ingestion pipeline.
- `pdf_parser.py` is intentionally stubbed until PDF support is implemented.
