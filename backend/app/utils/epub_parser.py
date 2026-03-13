from __future__ import annotations

import logging

from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub

logger = logging.getLogger(__name__)


class EpubParser:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def extract(self) -> list[dict]:
        book = epub.read_epub(self.filepath)
        chapters: list[dict] = []

        for chapter_index, spine_item in enumerate(book.spine):
            item_id = spine_item[0] if isinstance(spine_item, tuple) else spine_item
            item = book.get_item_with_id(item_id)
            if item is None or item.get_type() != ITEM_DOCUMENT:
                continue

            soup = BeautifulSoup(item.get_body_content(), "html.parser")
            text = soup.get_text(" ", strip=True)
            if not text:
                logger.warning("Skipping empty spine item: %s", item_id)
                continue

            chapters.append(
                {
                    "chapter_index": chapter_index,
                    "title": item.get_name(),
                    "text": text,
                }
            )

        return chapters
