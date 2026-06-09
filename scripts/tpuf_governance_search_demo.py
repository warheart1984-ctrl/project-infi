"""Index AAIS governance contracts into Turbopuffer and run BM25 retrieval.

Demonstrates Turbopuffer as a docs_v1 retrieval projection aligned with
memory_vector_store.py (384-dim MiniLM embeddings + full-text search).

Requires: TURBOPUFFER_API_KEY in the environment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "docs" / "contracts"
NAMESPACE = "project-infi-governance"
EMBED_DIM = 384
DEMO_QUERY = "Can a vector database replace constitutional truth or operator ledgers?"

TARGET_FILES = [
    "MEMORY_VECTOR_BACKEND_ADMISSION.md",
    "JARVIS_MEMORY_BOARD_DOCTRINE.md",
    "EXTERNAL_SUGGESTION_ADMISSION_RULE.md",
    "AAIS_ADAPTIVE_GOVERNANCE.md",
    "NARRATIVE_CONTINUITY_CONTRACT.md",
    "IDENTITY_SELF_MODEL_CONTRACT.md",
]


def load_chunks() -> list[dict]:
    rows: list[dict] = []
    row_id = 1
    for name in TARGET_FILES:
        path = CONTRACTS / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        rows.append(
            {
                "id": row_id,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "title": name.replace(".md", "").replace("_", " "),
                "content": text[:12000],
                "doc_type": "contract",
            }
        )
        row_id += 1
    return rows


def embed(texts: list[str]) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def main() -> int:
    api_key = os.getenv("TURBOPUFFER_API_KEY", "").strip()
    if not api_key:
        print("TURBOPUFFER_API_KEY is not set.")
        print("Get a key at https://turbopuffer.com/dashboard")
        print("Then: $env:TURBOPUFFER_API_KEY='tpuf_...'  (PowerShell)")
        return 1

    import turbopuffer as tpuf

    rows = load_chunks()
    if not rows:
        print("No contract files found under docs/contracts/")
        return 1

    texts = [f"{r['title']}\n{r['content']}" for r in rows]
    vectors = embed(texts)
    for row, vector in zip(rows, vectors):
        row["vector"] = vector

    client = tpuf.Turbopuffer(api_key=api_key)
    ns = client.namespace(NAMESPACE)
    result = ns.write(
        upsert_rows=rows,
        distance_metric="cosine_distance",
        schema={
            "content": {"type": "string", "full_text_search": True},
            "title": {"type": "string", "full_text_search": True},
            "path": {"type": "string", "filterable": True},
            "doc_type": {"type": "string", "filterable": True},
            "vector": {"type": f"[{EMBED_DIM}]f32", "ann": True},
        },
    )
    print(f"Upserted {result.rows_affected} governance contracts into namespace '{NAMESPACE}'")

    bm25 = ns.query(
        rank_by=["content", "BM25", DEMO_QUERY],
        limit=3,
        include_attributes=["title", "path", "$dist"],
    )
    print(f"\nBM25 query: {DEMO_QUERY!r}\n")
    for row in bm25.rows or []:
        print(f"  - {row['title']} ({row['path']})")

    ann = ns.query(
        rank_by=["vector", "ANN", vectors[0]],
        limit=3,
        include_attributes=["title", "path"],
        filters=["doc_type", "Eq", "contract"],
    )
    print("\nANN neighbors of MEMORY_VECTOR_BACKEND_ADMISSION (filtered to contracts):")
    for row in ann.rows or []:
        print(f"  - {row['title']} ({row['path']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
