from pathlib import Path

from app.utils.epub_parser import EpubParser


def test_extract_returns_non_empty_list():
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "sample.epub"
    chapters = EpubParser(str(fixture)).extract()
    assert chapters


def test_extract_items_have_required_keys():
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "sample.epub"
    chapters = EpubParser(str(fixture)).extract()
    for chapter in chapters:
        assert {"chapter_index", "title", "text"} <= chapter.keys()


def test_text_is_clean_and_non_empty():
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "sample.epub"
    chapters = EpubParser(str(fixture)).extract()
    for chapter in chapters:
        assert chapter["text"].strip()
        assert "<" not in chapter["text"]
        assert ">" not in chapter["text"]


def test_chapters_are_in_order():
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "sample.epub"
    chapters = EpubParser(str(fixture)).extract()
    indices = [chapter["chapter_index"] for chapter in chapters]
    assert indices == sorted(indices)
