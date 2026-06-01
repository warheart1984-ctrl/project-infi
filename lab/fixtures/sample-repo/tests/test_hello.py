from src.hello import greet


def test_greet() -> None:
    assert greet("lab") == "hello, lab"
