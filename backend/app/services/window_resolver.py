def resolve(book_id: str, position_char: int, level: int) -> str:
    from app.bootstrap import get_container

    return get_container().window_resolver.resolve(book_id, position_char, level)
