from __future__ import annotations
import uuid
import chromadb
from chromadb.config import Settings
from app.config import CHROMA_DIR

_client = chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))
_memory_collection = _client.get_or_create_collection(name="jarvis_memory")
_docs_collection = _client.get_or_create_collection(name="jarvis_docs")

def should_store_memory(text: str) -> bool:
    lowered = text.lower()
    durable_signals = ["my name is", "i like ", "i prefer ", "goal:", "project", "remember", "final response:", "conversation summary:"]
    return any(sig in lowered for sig in durable_signals) or (40 <= len(text) <= 1000)

def store_memory(text: str, session_id: str = "default") -> None:
    if not text.strip() or not should_store_memory(text):
        return
    _memory_collection.add(
        ids=[str(uuid.uuid4())],
        documents=[text],
        metadatas=[{"source": "chat", "session_id": session_id}],
    )

def retrieve_memory(query: str, session_id: str = "default", n_results: int = 4) -> list[str]:
    if not query.strip():
        return []
    results = _memory_collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"session_id": session_id},
    )
    docs = results.get("documents", [[]])
    return docs[0] if docs else []

def clear_docs() -> None:
    global _docs_collection
    _client.delete_collection("jarvis_docs")
    _docs_collection = _client.get_or_create_collection(name="jarvis_docs")

def add_doc_chunks(chunks: list[str], metas: list[dict]) -> int:
    if not chunks:
        return 0
    ids = [str(uuid.uuid4()) for _ in chunks]
    _docs_collection.add(ids=ids, documents=chunks, metadatas=metas)
    return len(chunks)

def query_docs(question: str, n_results: int = 4) -> list[str]:
    if not question.strip():
        return []
    results = _docs_collection.query(query_texts=[question], n_results=n_results)
    docs = results.get("documents", [[]])
    return docs[0] if docs else []
