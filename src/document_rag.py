"""Document/PDF analysis with RAG (Retrieval-Augmented Generation)

Optimized with embedding caching and batch encoding.
"""

# Mythic: Document Rag
# Engineering: DocumentRagEngine
from __future__ import annotations

import os
import hashlib
from pathlib import Path
import re
from src.logger import get_logger
from src.performance import timed

try:
    import numpy as np
except Exception as exc:  # pragma: no cover - exercised indirectly in fallback mode
    np = None
    _NUMPY_IMPORT_ERROR = exc
else:
    _NUMPY_IMPORT_ERROR = None

logger = get_logger(__name__)

DOCUMENT_ROLE_SOURCE_HINTS = (
    "source of truth",
    "canonical",
    "reference",
    "use this as input",
    "build from this",
)

DOCUMENT_ROLE_INPUT_ARTIFACT_HINTS = (
    "fix",
    "repair",
    "correct",
    "update this",
    "edit this",
    "revise",
    "patch this",
    "improve this",
)


def sanitize_document_text(text: str) -> str:
    """Normalize extracted text before it enters chunking or prompt assembly."""
    cleaned = str(text or "")
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def infer_document_role(input_text: str) -> str:
    """Infer how the operator intends Jarvis to treat one uploaded document."""
    normalized = " ".join(str(input_text or "").lower().split()).strip()
    if any(phrase in normalized for phrase in DOCUMENT_ROLE_SOURCE_HINTS):
        return "source_of_truth"
    if any(phrase in normalized for phrase in DOCUMENT_ROLE_INPUT_ARTIFACT_HINTS):
        return "input_artifact"
    return "context"


def _import_optional(module_name, package=None):
    """Import an optional dependency, returning None if unavailable."""
    try:
        import importlib
        return importlib.import_module(module_name, package)
    except ImportError:
        return None


class TextChunker:
    """Split text into overlapping chunks for embedding"""

    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list:
        """Split text into overlapping word-level chunks"""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunk_text = " ".join(words[start:end])
            chunks.append(chunk_text)
            start += self.chunk_size - self.overlap
        return chunks


class DocumentStore:
    """In-memory vector store with embedding caching"""

    def __init__(self):
        self.documents = {}
        self._embedding_model = None
        self._query_cache = {}  # LRU cache for query embeddings
        self._max_query_cache = 512
        self._fallback_notice_emitted = False

    def _log_fallback_once(self, reason: str) -> None:
        """Emit a single bounded warning when lexical fallback is active."""
        if self._fallback_notice_emitted:
            return
        logger.warning("Document RAG running in lexical fallback mode: %s", reason)
        self._fallback_notice_emitted = True

    def _vector_search_available(self) -> bool:
        """Return whether compiled embedding search is usable in this runtime."""
        return np is not None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Split text into normalized lexical tokens for fallback search."""
        return re.findall(r"[a-z0-9_]+", str(text or "").lower())

    def _lexical_score(self, query: str, chunk: str) -> float:
        """Compute a small deterministic overlap score when embeddings are unavailable."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return 0.0
        chunk_terms = set(self._tokenize(chunk))
        if not chunk_terms:
            return 0.0
        overlap = sum(1 for term in query_terms if term in chunk_terms)
        phrase_bonus = 0.25 if " ".join(query_terms) in str(chunk or "").lower() else 0.0
        return (overlap / max(len(set(query_terms)), 1)) + phrase_bonus

    def _get_embedding_model(self):
        """Lazy-load a sentence embedding model"""
        if not self._vector_search_available():
            reason = f"numpy unavailable ({_NUMPY_IMPORT_ERROR})" if _NUMPY_IMPORT_ERROR else "numpy unavailable"
            self._log_fallback_once(reason)
            return None
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded sentence embedding model: all-MiniLM-L6-v2")
            except ImportError:
                self._log_fallback_once("sentence-transformers unavailable")
                return None
        return self._embedding_model

    def _embed(self, texts: list, batch_size: int = 64):
        """Generate embeddings with batched encoding"""
        model = self._get_embedding_model()
        if model is None:
            return [None for _ in texts]
        return model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=batch_size,
        )

    def _embed_query(self, query: str):
        """Embed a query with caching"""
        model = self._get_embedding_model()
        if model is None:
            return None
        cache_key = hashlib.sha256(query.encode()).hexdigest()[:16]

        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        embedding = model.encode(
            [query],
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=1,
        )[0]

        # LRU eviction
        if len(self._query_cache) >= self._max_query_cache:
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]

        self._query_cache[cache_key] = embedding
        return embedding

    @timed
    def ingest_text(self, text: str, doc_id: str = None, metadata: dict = None) -> str:
        """Ingest raw text, chunk it, and store embeddings"""
        sanitized_text = sanitize_document_text(text)
        if not sanitized_text:
            raise ValueError("Document contained no usable text")

        if not doc_id:
            doc_id = hashlib.sha256(sanitized_text[:200].encode()).hexdigest()[:16]

        chunker = TextChunker()
        chunks = chunker.chunk(sanitized_text)
        if not chunks:
            raise ValueError("Document produced no chunks")

        embeddings = self._embed(chunks)

        self.documents[doc_id] = {
            "chunks": chunks,
            "embeddings": embeddings,
            "metadata": dict(metadata or {}),
        }
        logger.info(f"Ingested document {doc_id}: {len(chunks)} chunks")
        return doc_id

    def ingest_pdf(self, pdf_path: str, doc_id: str = None, metadata: dict = None) -> str:
        """Extract text from a PDF and ingest it"""
        PyPDF2 = _import_optional("PyPDF2")
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is required for PDF ingestion. pip install PyPDF2")

        reader = PyPDF2.PdfReader(pdf_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        full_text = "\n".join(pages_text)
        if not full_text.strip():
            raise ValueError("PDF contained no extractable text")

        resolved_metadata = dict(metadata or {})
        resolved_metadata.update({"source": str(pdf_path), "type": "pdf", "pages": len(reader.pages)})
        return self.ingest_text(full_text, doc_id=doc_id, metadata=resolved_metadata)

    def ingest_url(self, url: str, doc_id: str = None, metadata: dict = None) -> str:
        """Fetch a URL and ingest its text content"""
        requests_mod = _import_optional("requests")
        bs4 = _import_optional("bs4")
        if requests_mod is None or bs4 is None:
            raise ImportError("requests and beautifulsoup4 are required")

        response = requests_mod.get(url, timeout=30)
        response.raise_for_status()

        soup = bs4.BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        if not text.strip():
            raise ValueError("URL contained no extractable text")

        resolved_metadata = dict(metadata or {})
        resolved_metadata.update({"source": url, "type": "url"})
        return self.ingest_text(text, doc_id=doc_id, metadata=resolved_metadata)

    @timed
    def search(self, query: str, top_k: int = 5, doc_id: str = None) -> list:
        """Search with cached query embeddings"""
        query_embedding = self._embed_query(query)
        results = []

        docs_to_search = (
            {doc_id: self.documents[doc_id]}
            if doc_id and doc_id in self.documents
            else self.documents
        )

        for did, doc in docs_to_search.items():
            embeddings = doc.get("embeddings") or []
            can_vector_search = (
                query_embedding is not None
                and np is not None
                and bool(embeddings)
                and all(embedding is not None for embedding in embeddings)
            )

            if can_vector_search:
                similarities = np.dot(embeddings, query_embedding)
                top_indices = np.argsort(similarities)[::-1][:top_k]
                for idx in top_indices:
                    results.append({
                        "doc_id": did,
                        "chunk": doc["chunks"][idx],
                        "score": float(similarities[idx]),
                        "metadata": doc["metadata"],
                    })
                continue

            for idx, chunk in enumerate(doc.get("chunks") or []):
                score = self._lexical_score(query, chunk)
                if score <= 0:
                    continue
                results.append(
                    {
                        "doc_id": did,
                        "chunk": chunk,
                        "score": float(score),
                        "metadata": doc.get("metadata") or {},
                    }
                )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self.documents:
            del self.documents[doc_id]
            logger.info(f"Deleted document: {doc_id}")
            return True
        return False

    def list_documents(self) -> list:
        return [
            {
                "doc_id": did,
                "chunk_count": len(doc["chunks"]),
                "metadata": doc["metadata"],
            }
            for did, doc in self.documents.items()
        ]


def build_rag_prompt(query: str, context_chunks: list) -> str:
    """Build a prompt that includes retrieved context for grounded generation"""
    context_block = "\n\n---\n\n".join(
        f"[Source: {c['metadata'].get('source', c['doc_id'])}]\n{c['chunk']}"
        for c in context_chunks
    )
    return (
        f"Use the following context to answer the question. "
        f"If the context does not contain the answer, say so.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\nAnswer:"
    )


document_store = DocumentStore()
