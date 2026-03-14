# `readers/`

This folder contains reader implementations and reader selection helpers.

## Contents

- `EpubReader.jsx`: EPUB rendering wrapper built on `epubjs`.
- `PdfReader.jsx`: PDF reader stub for future support.
- `BookReaderFactory.js`: chooses the reader type based on filename extension.

## Notes

- `EpubReader.jsx` is the active implementation today.
- `PdfReader.jsx` exists to preserve a compatible interface for future work.
