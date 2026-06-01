from __future__ import annotations
from pathlib import Path
from app.config import BASE_DIR
from app.memory import clear_docs, add_doc_chunks, query_docs

TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".html", ".css", ".sql", ".csv"
}

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks

def index_project(path_text: str = "") -> tuple[int, int]:
    root = (BASE_DIR / path_text).resolve() if path_text.strip() else BASE_DIR.resolve()
    base = BASE_DIR.resolve()
    if base not in root.parents and root != base:
        raise ValueError("Path is outside allowed project directory.")
    if not root.exists():
        raise ValueError("Path not found.")

    clear_docs()
    indexed_files = 0
    indexed_chunks = 0

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            if file_path.stat().st_size > 200_000:
                continue
            text = file_path.read_text(encoding="utf-8", errors="replace")
            chunks = chunk_text(text)
            metas = [{"path": str(file_path.relative_to(BASE_DIR)), "chunk_index": i} for i, _ in enumerate(chunks)]
            indexed_chunks += add_doc_chunks(chunks, metas)
            indexed_files += 1
        except Exception:
            continue

    return indexed_files, indexed_chunks

def query_project(question: str, n_results: int = 4) -> list[str]:
    return query_docs(question, n_results=n_results)
