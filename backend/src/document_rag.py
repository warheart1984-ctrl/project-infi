"""Document/PDF analysis with RAG (Retrieval-Augmented Generation)

Optimized with embedding caching and batch encoding.
"""

import os
import hashlib
import numpy as np
from pathlib import Path
from src.logger import get_logger
from src.performance import timed

logger = get_logger(__name__)


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

    def _get_embedding_model(self):
        """Lazy-load a sentence embedding model"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded sentence embedding model: all-MiniLM-L6-v2")
            except ImportError:
                raise ImportError("sentence-transformers is required for RAG")
        return self._embedding_model

    def _embed(self, texts: list, batch_size: int = 64) -> np.ndarray:
        """Generate embeddings with batched encoding"""
        model = self._get_embedding_model()
        return model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=batch_size,
        )

    def _embed_query(self, query: str) -> np.ndarray:
        """Embed a query with caching"""
        cache_key = hashlib.sha256(query.encode()).hexdigest()[:16]

        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        embedding = self._embed([query])[0]

        # LRU eviction
        if len(self._query_cache) >= self._max_query_cache:
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]

        self._query_cache[cache_key] = embedding
        return embedding

    @timed
    def ingest_text(self, text: str, doc_id: str = None, metadata: dict = None) -> str:
        """Ingest raw text, chunk it, and store embeddings"""
        if not doc_id:
            doc_id = hashlib.sha256(text[:200].encode()).hexdigest()[:16]

        chunker = TextChunker()
        chunks = chunker.chunk(text)
        if not chunks:
            raise ValueError("Document produced no chunks")

        embeddings = self._embed(chunks)

        self.documents[doc_id] = {
            "chunks": chunks,
            "embeddings": embeddings,
            "metadata": metadata or {},
        }
        logger.info(f"Ingested document {doc_id}: {len(chunks)} chunks")
        return doc_id

    def ingest_pdf(self, pdf_path: str, doc_id: str = None) -> str:
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

        metadata = {"source": str(pdf_path), "type": "pdf", "pages": len(reader.pages)}
        return self.ingest_text(full_text, doc_id=doc_id, metadata=metadata)

    def ingest_url(self, url: str, doc_id: str = None) -> str:
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

        metadata = {"source": url, "type": "url"}
        return self.ingest_text(text, doc_id=doc_id, metadata=metadata)

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
            similarities = np.dot(doc["embeddings"], query_embedding)
            top_indices = np.argsort(similarities)[::-1][:top_k]
            for idx in top_indices:
                results.append({
                    "doc_id": did,
                    "chunk": doc["chunks"][idx],
                    "score": float(similarities[idx]),
                    "metadata": doc["metadata"],
                })

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
