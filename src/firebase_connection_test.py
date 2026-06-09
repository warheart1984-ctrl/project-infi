"""Minimal Firebase Data Connect connectivity smoke test."""

from __future__ import annotations

import sys

from src.firebase_dataconnect_client import execute_query, firebase_configured, rows_from_query


def main() -> int:
    if not firebase_configured():
        print(
            "Firebase Data Connect is not configured. Set FIREBASE_PROJECT_ID "
            "(and GOOGLE_APPLICATION_CREDENTIALS, or DATA_CONNECT_EMULATOR_HOST)."
        )
        return 1
    try:
        payload = execute_query(
            "RetrieveMemorySimilarityDocs",
            {
                "tenantId": "default",
                "memorySlot": "docs_v1",
                "queryVector": [0.0] * 384,
                "limit": 1,
            },
        )
        rows = rows_from_query(payload, "memoryChunks_embedding_similarity")
        print(f"Connected. RetrieveMemorySimilarityDocs returned {len(rows)} row(s).")
        return 0
    except Exception as exc:
        print(f"Connection failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
