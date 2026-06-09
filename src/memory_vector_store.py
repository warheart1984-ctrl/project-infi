"""Governed vector store adapter for Jarvis Memory Board retrieval.

Supports Chroma (default, local-first), ScyllaDB Cloud Vector Search projection,
and Firebase Data Connect (PostgreSQL + pgvector) projection.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

EMBEDDING_DIMENSIONS = 384
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_MEMORY_SLOT = "session_v1"
DOCS_MEMORY_SLOT = "docs_v1"
DEFAULT_TENANT_ID = "default"
DEFAULT_CISIV_STAGE = "implementation"

SLOT_CLASS_TO_MEMORY_SLOT = {
    "foundation": "foundation_v1",
    "operational": "operational_v1",
    "session": "session_v1",
    "archive": "archive_v1",
    "signal": "signal_v1",
    "preference": "preference_v1",
}

SLOT_ID_TO_MEMORY_SLOT = {
    "slot_01": "foundation_v1",
    "slot_02": "operational_v1",
    "slot_03": "session_v1",
    "slot_04": "archive_v1",
    "slot_05": "signal_v1",
    "slot_06": "preference_v1",
}


def vector_backend_name() -> str:
    return os.getenv("AAIS_VECTOR_BACKEND", "chroma").strip().lower()


def tenant_id() -> str:
    return os.getenv("AAIS_VECTOR_TENANT_ID", DEFAULT_TENANT_ID).strip() or DEFAULT_TENANT_ID


def memory_slot_for_slot_id(slot_id: str) -> str:
    return SLOT_ID_TO_MEMORY_SLOT.get(slot_id, DEFAULT_MEMORY_SLOT)


def memory_slot_for_module_class(module_class: str) -> str:
    return SLOT_CLASS_TO_MEMORY_SLOT.get(module_class, DEFAULT_MEMORY_SLOT)


def should_store_memory(text: str) -> bool:
    lowered = text.lower()
    durable_signals = [
        "my name is",
        "i like ",
        "i prefer ",
        "goal:",
        "project",
        "remember",
        "final response:",
        "conversation summary:",
    ]
    return any(sig in lowered for sig in durable_signals) or (40 <= len(text) <= 1000)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _embed_texts(texts: list[str]) -> list[list[float] | None]:
    try:
        import numpy as np
    except ImportError:
        return [None for _ in texts]
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return [None for _ in texts]
    model = SentenceTransformer(EMBEDDING_MODEL)
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return [vector.tolist() for vector in np.asarray(vectors)]


def _embed_query(query: str) -> list[float] | None:
    vectors = _embed_texts([query])
    return vectors[0] if vectors else None


@dataclass(frozen=True, slots=True)
class MemoryChunkMeta:
    session_id: str = "default"
    memory_slot: str = DEFAULT_MEMORY_SLOT
    trust_class: str = "working"
    source: str = "chat"
    tenant_id: str = DEFAULT_TENANT_ID
    cisiv_stage: str = DEFAULT_CISIV_STAGE

    def as_dict(self) -> dict[str, str]:
        return {
            "session_id": self.session_id,
            "memory_slot": self.memory_slot,
            "trust_class": self.trust_class,
            "source": self.source,
            "tenant_id": self.tenant_id,
            "cisiv_stage": self.cisiv_stage,
        }


class VectorStoreBackend(Protocol):
    def store_memory(self, text: str, meta: MemoryChunkMeta) -> None: ...
    def retrieve_memory(
        self,
        query: str,
        *,
        session_id: str = "default",
        memory_slot: str = DEFAULT_MEMORY_SLOT,
        trust_class: str | None = None,
        n_results: int = 4,
    ) -> list[str]: ...
    def clear_docs(self) -> None: ...
    def add_doc_chunks(self, chunks: list[str], metas: list[dict]) -> int: ...
    def query_docs(self, question: str, n_results: int = 4) -> list[str]: ...


class ChromaVectorBackend:
    def __init__(self, chroma_dir: str) -> None:
        import chromadb
        from chromadb.config import Settings

        self._client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._memory_collection = self._client.get_or_create_collection(name="jarvis_memory")
        self._docs_collection = self._client.get_or_create_collection(name="jarvis_docs")

    def store_memory(self, text: str, meta: MemoryChunkMeta) -> None:
        self._memory_collection.add(
            ids=[str(uuid.uuid4())],
            documents=[text],
            metadatas=[meta.as_dict()],
        )

    @staticmethod
    def _chroma_where(filters: dict[str, str]) -> dict[str, Any]:
        clauses = [{key: value} for key, value in filters.items()]
        if not clauses:
            return {}
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    def retrieve_memory(
        self,
        query: str,
        *,
        session_id: str = "default",
        memory_slot: str = DEFAULT_MEMORY_SLOT,
        trust_class: str | None = None,
        n_results: int = 4,
    ) -> list[str]:
        if not query.strip():
            return []
        filters = {
            "session_id": session_id,
            "memory_slot": memory_slot,
        }
        if trust_class:
            filters["trust_class"] = trust_class
        results = self._memory_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=self._chroma_where(filters),
        )
        docs = results.get("documents", [[]])
        return docs[0] if docs else []

    def clear_docs(self) -> None:
        self._client.delete_collection("jarvis_docs")
        self._docs_collection = self._client.get_or_create_collection(name="jarvis_docs")

    def add_doc_chunks(self, chunks: list[str], metas: list[dict]) -> int:
        if not chunks:
            return 0
        enriched: list[dict] = []
        for meta in metas:
            row = dict(meta)
            row.setdefault("memory_slot", DOCS_MEMORY_SLOT)
            row.setdefault("tenant_id", tenant_id())
            row.setdefault("source", row.get("path", "docs"))
            enriched.append(row)
        ids = [str(uuid.uuid4()) for _ in chunks]
        self._docs_collection.add(ids=ids, documents=chunks, metadatas=enriched)
        return len(chunks)

    def query_docs(self, question: str, n_results: int = 4) -> list[str]:
        if not question.strip():
            return []
        results = self._docs_collection.query(
            query_texts=[question],
            n_results=n_results,
            where=self._chroma_where({"memory_slot": DOCS_MEMORY_SLOT}),
        )
        docs = results.get("documents", [[]])
        return docs[0] if docs else []


_scylla_cluster = None
_scylla_session = None


def scylla_configured() -> bool:
    return bool(
        os.getenv("SCYLLA_CONTACT_POINTS", "").strip()
        and os.getenv("SCYLLA_LOCAL_DC", "").strip()
    )


def scylla_session():
    global _scylla_cluster, _scylla_session
    if _scylla_session is not None:
        return _scylla_session
    if not scylla_configured():
        raise RuntimeError("ScyllaDB is not configured (SCYLLA_CONTACT_POINTS, SCYLLA_LOCAL_DC).")
    try:
        from cassandra.auth import PlainTextAuthProvider
        from cassandra.cluster import Cluster
        from cassandra.policies import DCAwareRoundRobinPolicy
    except ImportError as exc:
        raise RuntimeError("scylla-driver is required for AAIS_VECTOR_BACKEND=scylladb") from exc

    contact_points = [
        point.strip()
        for point in os.getenv("SCYLLA_CONTACT_POINTS", "").split(",")
        if point.strip()
    ]
    auth = PlainTextAuthProvider(
        username=os.getenv("SCYLLA_USERNAME", "scylla"),
        password=os.getenv("SCYLLA_PASSWORD", ""),
    )
    local_dc = os.getenv("SCYLLA_LOCAL_DC", "").strip()
    port = int(os.getenv("SCYLLA_PORT", "9042"))
    keyspace = os.getenv("SCYLLA_KEYSPACE", "jarvis_memory").strip()

    _scylla_cluster = Cluster(
        contact_points=contact_points,
        port=port,
        auth_provider=auth,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=local_dc),
    )
    _scylla_session = _scylla_cluster.connect(keyspace)
    return _scylla_session


class ScyllaVectorBackend:
    def store_memory(self, text: str, meta: MemoryChunkMeta) -> None:
        embedding = _embed_query(text)
        if embedding is None:
            raise RuntimeError("Embedding model unavailable for ScyllaDB vector store.")
        session = scylla_session()
        session.execute(
            """
            INSERT INTO memory_chunks (
                tenant_id, memory_slot, chunk_id, session_id, trust_class,
                source, text_body, embedding, recorded_at, cisiv_stage
            ) VALUES (%s, %s, now(), %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                meta.tenant_id,
                meta.memory_slot,
                meta.session_id,
                meta.trust_class,
                meta.source,
                text,
                embedding,
                _utc_now(),
                meta.cisiv_stage,
            ),
        )

    def retrieve_memory(
        self,
        query: str,
        *,
        session_id: str = "default",
        memory_slot: str = DEFAULT_MEMORY_SLOT,
        trust_class: str | None = None,
        n_results: int = 4,
    ) -> list[str]:
        if not query.strip():
            return []
        query_vec = _embed_query(query)
        if query_vec is None:
            return []
        session = scylla_session()
        cql = """
            SELECT text_body
            FROM memory_chunks
            WHERE tenant_id = %s AND memory_slot = %s AND session_id = %s
            ORDER BY embedding ANN OF %s LIMIT %s
        """
        rows = session.execute(
            cql,
            (tenant_id(), memory_slot, session_id, query_vec, n_results),
        )
        results = [row.text_body for row in rows]
        if trust_class:
            # Post-filter when trust_class constraint is required beyond ANN ranking.
            filtered_rows = session.execute(
                """
                SELECT text_body, trust_class
                FROM memory_chunks
                WHERE tenant_id = %s AND memory_slot = %s AND session_id = %s
                ORDER BY embedding ANN OF %s LIMIT %s
                """,
                (tenant_id(), memory_slot, session_id, query_vec, max(n_results * 3, n_results)),
            )
            results = [
                row.text_body
                for row in filtered_rows
                if row.trust_class == trust_class
            ][:n_results]
        return results

    def clear_docs(self) -> None:
        session = scylla_session()
        session.execute(
            "DELETE FROM memory_chunks WHERE tenant_id = %s AND memory_slot = %s",
            (tenant_id(), DOCS_MEMORY_SLOT),
        )

    def add_doc_chunks(self, chunks: list[str], metas: list[dict]) -> int:
        if not chunks:
            return 0
        embeddings = _embed_texts(chunks)
        session = scylla_session()
        stored = 0
        for chunk, meta, embedding in zip(chunks, metas, embeddings):
            if embedding is None:
                continue
            session.execute(
                """
                INSERT INTO memory_chunks (
                    tenant_id, memory_slot, chunk_id, session_id, trust_class,
                    source, text_body, embedding, recorded_at, cisiv_stage
                ) VALUES (%s, %s, now(), %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    tenant_id(),
                    DOCS_MEMORY_SLOT,
                    str(meta.get("session_id", "default")),
                    str(meta.get("trust_class", "verified")),
                    str(meta.get("source", meta.get("path", "docs"))),
                    chunk,
                    embedding,
                    _utc_now(),
                    str(meta.get("cisiv_stage", DEFAULT_CISIV_STAGE)),
                ),
            )
            stored += 1
        return stored

    def query_docs(self, question: str, n_results: int = 4) -> list[str]:
        if not question.strip():
            return []
        query_vec = _embed_query(question)
        if query_vec is None:
            return []
        session = scylla_session()
        rows = session.execute(
            """
            SELECT text_body
            FROM memory_chunks
            WHERE tenant_id = %s AND memory_slot = %s
            ORDER BY embedding ANN OF %s LIMIT %s
            """,
            (tenant_id(), DOCS_MEMORY_SLOT, query_vec, n_results),
        )
        return [row.text_body for row in rows]


class FirebaseDataConnectVectorBackend:
    def _require_embedding(self, text: str) -> list[float]:
        embedding = _embed_query(text)
        if embedding is None:
            raise RuntimeError("Embedding model unavailable for Firebase Data Connect vector store.")
        return embedding

    def store_memory(self, text: str, meta: MemoryChunkMeta) -> None:
        from src.firebase_dataconnect_client import execute_mutation

        execute_mutation(
            "StoreMemoryChunk",
            {
                "tenantId": meta.tenant_id,
                "memorySlot": meta.memory_slot,
                "sessionId": meta.session_id,
                "trustClass": meta.trust_class,
                "source": meta.source,
                "textBody": text,
                "embedding": self._require_embedding(text),
                "cisivStage": meta.cisiv_stage,
            },
        )

    def retrieve_memory(
        self,
        query: str,
        *,
        session_id: str = "default",
        memory_slot: str = DEFAULT_MEMORY_SLOT,
        trust_class: str | None = None,
        n_results: int = 4,
    ) -> list[str]:
        if not query.strip():
            return []
        from src.firebase_dataconnect_client import execute_query, rows_from_query

        query_vec = _embed_query(query)
        if query_vec is None:
            return []
        if trust_class:
            operation = "RetrieveMemorySimilarityVerified"
            variables = {
                "tenantId": tenant_id(),
                "memorySlot": memory_slot,
                "sessionId": session_id,
                "trustClass": trust_class,
                "queryVector": query_vec,
                "limit": n_results,
            }
            field = "memoryChunks_embedding_similarity"
        else:
            operation = "RetrieveMemorySimilarity"
            variables = {
                "tenantId": tenant_id(),
                "memorySlot": memory_slot,
                "sessionId": session_id,
                "queryVector": query_vec,
                "limit": n_results,
            }
            field = "memoryChunks_embedding_similarity"

        payload = execute_query(operation, variables)
        return [
            str(row.get("textBody", ""))
            for row in rows_from_query(payload, field)
            if row.get("textBody")
        ]

    def clear_docs(self) -> None:
        from src.firebase_dataconnect_client import execute_mutation

        execute_mutation(
            "DeleteMemoryChunksBySlot",
            {
                "tenantId": tenant_id(),
                "memorySlot": DOCS_MEMORY_SLOT,
            },
        )

    def add_doc_chunks(self, chunks: list[str], metas: list[dict]) -> int:
        if not chunks:
            return 0
        from src.firebase_dataconnect_client import execute_mutation

        embeddings = _embed_texts(chunks)
        stored = 0
        for chunk, meta, embedding in zip(chunks, metas, embeddings):
            if embedding is None:
                continue
            execute_mutation(
                "StoreMemoryChunk",
                {
                    "tenantId": tenant_id(),
                    "memorySlot": DOCS_MEMORY_SLOT,
                    "sessionId": str(meta.get("session_id", "default")),
                    "trustClass": str(meta.get("trust_class", "verified")),
                    "source": str(meta.get("source", meta.get("path", "docs"))),
                    "textBody": chunk,
                    "embedding": embedding,
                    "cisivStage": str(meta.get("cisiv_stage", DEFAULT_CISIV_STAGE)),
                },
            )
            stored += 1
        return stored

    def query_docs(self, question: str, n_results: int = 4) -> list[str]:
        if not question.strip():
            return []
        from src.firebase_dataconnect_client import execute_query, rows_from_query

        query_vec = _embed_query(question)
        if query_vec is None:
            return []
        payload = execute_query(
            "RetrieveMemorySimilarityDocs",
            {
                "tenantId": tenant_id(),
                "memorySlot": DOCS_MEMORY_SLOT,
                "queryVector": query_vec,
                "limit": n_results,
            },
        )
        return [
            str(row.get("textBody", ""))
            for row in rows_from_query(payload, "memoryChunks_embedding_similarity")
            if row.get("textBody")
        ]


_backend: VectorStoreBackend | None = None


def _resolve_chroma_dir() -> str:
    from app.config import CHROMA_DIR

    return str(CHROMA_DIR)


def get_backend() -> VectorStoreBackend:
    global _backend
    if _backend is not None:
        return _backend
    backend = vector_backend_name()
    if backend == "firebase":
        from src.firebase_dataconnect_client import firebase_configured

        if not firebase_configured():
            raise RuntimeError(
                "AAIS_VECTOR_BACKEND=firebase requires FIREBASE_PROJECT_ID "
                "(and Google credentials unless DATA_CONNECT_EMULATOR_HOST is set)."
            )
        _backend = FirebaseDataConnectVectorBackend()
    elif backend == "scylladb":
        _backend = ScyllaVectorBackend()
    else:
        _backend = ChromaVectorBackend(_resolve_chroma_dir())
    return _backend


def reset_backend_for_tests() -> None:
    global _backend, _scylla_cluster, _scylla_session
    _backend = None
    _scylla_cluster = None
    _scylla_session = None


def store_memory(
    text: str,
    session_id: str = "default",
    *,
    memory_slot: str = DEFAULT_MEMORY_SLOT,
    trust_class: str = "working",
    source: str = "chat",
    cisiv_stage: str = DEFAULT_CISIV_STAGE,
) -> None:
    if not text.strip() or not should_store_memory(text):
        return
    meta = MemoryChunkMeta(
        session_id=session_id,
        memory_slot=memory_slot,
        trust_class=trust_class,
        source=source,
        tenant_id=tenant_id(),
        cisiv_stage=cisiv_stage,
    )
    get_backend().store_memory(text, meta)


def retrieve_memory(
    query: str,
    session_id: str = "default",
    *,
    memory_slot: str = DEFAULT_MEMORY_SLOT,
    trust_class: str | None = None,
    n_results: int = 4,
) -> list[str]:
    return get_backend().retrieve_memory(
        query,
        session_id=session_id,
        memory_slot=memory_slot,
        trust_class=trust_class,
        n_results=n_results,
    )


def clear_docs() -> None:
    get_backend().clear_docs()


def add_doc_chunks(chunks: list[str], metas: list[dict]) -> int:
    return get_backend().add_doc_chunks(chunks, metas)


def query_docs(question: str, n_results: int = 4) -> list[str]:
    return get_backend().query_docs(question, n_results=n_results)
