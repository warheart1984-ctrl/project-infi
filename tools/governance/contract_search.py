#!/usr/bin/env python3
"""BM25 search over docs/contracts using ParadeDB pg_search.

Indexes governance contract markdown into Postgres and ranks matches with BM25.
Requires ParadeDB (paradedb/paradedb image) — see deploy/platform/docker-compose.yml.

Usage:
  python tools/governance/contract_search.py index
  python tools/governance/contract_search.py search "contextual gates tier5 operator lanes"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = _ROOT / "docs" / "contracts"
DEFAULT_DATABASE_URL = os.environ.get(
    "PLATFORM_DATABASE_URL",
    "postgresql://platform:platform@127.0.0.1:5433/platform",
)


def _connect(database_url: str):
    try:
        import psycopg  # type: ignore[import-not-found]
        from psycopg.rows import dict_row  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("psycopg is required: pip install psycopg[binary]") from exc
    return psycopg.connect(database_url, row_factory=dict_row)


def _title_from_markdown(path: Path, body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("_", " ")


def _load_contracts() -> list[tuple[str, str, str]]:
    docs: list[tuple[str, str, str]] = []
    for path in sorted(CONTRACTS_DIR.glob("*.md")):
        body = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(_ROOT).as_posix()
        docs.append((rel, _title_from_markdown(path, body), body))
    return docs


def _ensure_schema(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contract_docs (
            doc_id SERIAL PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            body TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _ensure_bm25_index(conn) -> None:
    row = conn.execute(
        """
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'contract_docs' AND indexname = 'idx_contract_docs_bm25'
        """
    ).fetchone()
    if row:
        return
    conn.execute(
        """
        CREATE INDEX idx_contract_docs_bm25 ON contract_docs
        USING bm25 (
            doc_id,
            title::pdb.simple('stemmer=english'),
            body::pdb.simple('stemmer=english')
        )
        WITH (key_field=doc_id)
        """
    )
    conn.commit()


def index_contracts(*, database_url: str) -> int:
    docs = _load_contracts()
    if not docs:
        print("[contract-search] no markdown files under docs/contracts")
        return 1

    with _connect(database_url) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS pg_search")
        conn.commit()
        _ensure_schema(conn)
        conn.execute("TRUNCATE contract_docs RESTART IDENTITY")
        for rel, title, body in docs:
            conn.execute(
                "INSERT INTO contract_docs (path, title, body) VALUES (%s, %s, %s)",
                (rel, title, body),
            )
        conn.commit()
        _ensure_bm25_index(conn)

    print(f"[contract-search] indexed {len(docs)} contracts at {database_url}")
    return 0


def search_contracts(*, database_url: str, query: str, limit: int = 8) -> int:
    q = re.sub(r"\s+", " ", query.strip())
    if not q:
        print("[contract-search] query required")
        return 1

    sql = """
        SELECT path, title, pdb.score(doc_id) AS score
        FROM contract_docs
        WHERE
            title ||| %(q)s::boost(2)
            OR body ||| %(q)s
        ORDER BY score DESC
        LIMIT %(limit)s
    """
    with _connect(database_url) as conn:
        rows = conn.execute(sql, {"q": q, "limit": limit}).fetchall()

    if not rows:
        print(f"[contract-search] no BM25 hits for: {q!r}")
        return 0

    print(f"[contract-search] top {len(rows)} for: {q!r}\n")
    for row in rows:
        score = float(row["score"])
        print(f"  {score:8.3f}  {row['path']}")
        print(f"             {row['title']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ParadeDB BM25 search over governance contracts")
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="Postgres URL (ParadeDB image required for pg_search)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("index", help="Rebuild contract_docs table and BM25 index")

    search_p = sub.add_parser("search", help="BM25 search contracts")
    search_p.add_argument("query", help="Search terms (stemmed English BM25)")
    search_p.add_argument("--limit", type=int, default=8)

    args = parser.parse_args(argv)
    if args.command == "index":
        return index_contracts(database_url=args.database_url)
    return search_contracts(database_url=args.database_url, query=args.query, limit=args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
