from app.utils.token_counter import count


def test_count_returns_positive_integer():
    assert count("hello world") > 0


def test_longer_text_has_higher_token_count():
    short = count("hello")
    long = count("hello world " * 20)
    assert long > short


def test_count_is_deterministic():
    text = "repeatable token count"
    assert count(text) == count(text)
