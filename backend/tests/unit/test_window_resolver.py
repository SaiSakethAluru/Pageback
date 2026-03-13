from types import SimpleNamespace

from app.services import window_resolver


class QueryBuilder:
    def __init__(self, rows):
        self.rows = rows

    def select(self, _fields):
        return self

    def eq(self, _field, _value):
        return self

    def lte(self, _field, _value):
        return self

    def order(self, _field, desc=False):
        if desc:
            self.rows = sorted(self.rows, key=lambda row: row["end_char"], reverse=True)
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class SupabaseStub:
    def __init__(self, rows):
        self.rows = rows
        self.rpc_calls = []

    def table(self, _name):
        return QueryBuilder(self.rows)

    def rpc(self, name, params):
        self.rpc_calls.append((name, params))
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=self.rows))


def test_level_one_uses_150_token_budget(monkeypatch):
    rows = [
        {"text": "first", "token_count": 100, "end_char": 100},
        {"text": "second", "token_count": 100, "end_char": 80},
    ]
    supabase = SupabaseStub(rows)
    monkeypatch.setattr(window_resolver, "_supabase", lambda: supabase)

    result = window_resolver.resolve("book", 100, 1)

    assert result == "first"


def test_spoiler_fence_is_respected(monkeypatch):
    rows = [
        {"text": "allowed", "token_count": 50, "end_char": 90},
        {"text": "blocked", "token_count": 50, "end_char": 150},
    ]
    supabase = SupabaseStub([rows[0]])
    monkeypatch.setattr(window_resolver, "_supabase", lambda: supabase)

    result = window_resolver.resolve("book", 100, 1)

    assert "blocked" not in result
    assert "allowed" in result


def test_levels_three_to_five_use_match_chunks(monkeypatch):
    rows = [
        {"text": "chunk one", "token_count": 100, "end_char": 90},
        {"text": "chunk two", "token_count": 100, "end_char": 95},
    ]
    supabase = SupabaseStub(rows)
    provider = SimpleNamespace(embed=lambda _text: [0.1, 0.2])
    monkeypatch.setattr(window_resolver, "_supabase", lambda: supabase)
    monkeypatch.setattr(window_resolver, "get_provider", lambda: provider)

    result = window_resolver.resolve("book", 100, 3)

    assert supabase.rpc_calls[0][0] == "match_chunks"
    assert supabase.rpc_calls[0][1]["p_book_id"] == "book"
    assert result == "chunk one\n\nchunk two"


def test_chunks_join_with_double_newlines(monkeypatch):
    rows = [
        {"text": "alpha", "token_count": 50, "end_char": 70},
        {"text": "beta", "token_count": 50, "end_char": 50},
    ]
    supabase = SupabaseStub(rows)
    monkeypatch.setattr(window_resolver, "_supabase", lambda: supabase)

    result = window_resolver.resolve("book", 100, 1)

    assert result == "alpha\n\nbeta"
