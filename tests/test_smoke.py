import pytest

pytest.importorskip("chromadb")

from app.tools import safe_calculate, list_files
from app.router import fast_route
from app.rag import chunk_text

def test_safe_calculate():
    assert safe_calculate("2+2") == "4"

def test_list_files():
    result = list_files("")
    assert isinstance(result, str)

def test_fast_route():
    assert fast_route("calc 2+2")[0] == "calculator"

def test_chunk_text():
    chunks = chunk_text("a" * 2500, chunk_size=1000, overlap=100)
    assert len(chunks) >= 3
