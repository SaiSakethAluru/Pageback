from app.services import recap_cache


def test_get_returns_none_on_miss():
    assert recap_cache.get("missing-key") is None


def test_set_and_get_round_trip():
    recap_cache.set("cache-key", "summary text")
    assert recap_cache.get("cache-key") == "summary text"


def test_expired_entry_returns_none():
    recap_cache.set("expired-key", "summary text", ttl_seconds=0)
    assert recap_cache.get("expired-key") is None


def test_make_key_is_stable():
    assert recap_cache.make_key("book", 10, 1) == recap_cache.make_key("book", 10, 1)


def test_make_key_changes_with_inputs():
    assert recap_cache.make_key("book", 10, 1) != recap_cache.make_key("book", 11, 1)
