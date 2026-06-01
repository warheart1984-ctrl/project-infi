"""SQLite graph query backend — rebuildable projection over canonical JSONL."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.ugr.graph_index.sync import discover_claim_paths, load_claims_from_paths
from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.unified_pattern_ledger import _stable_json


class SQLiteGraphBackend:
    """Embedded SQLite index for claim graph queries."""

    BACKEND_VERSION = "1.0"
    DRIVER = "sqlite"

    def __init__(self, *, runtime_root: str | Path, config: dict[str, Any] | None = None):
        self.runtime_root = Path(runtime_root)
        self.config = dict(config or {})
        self.db_path = self.runtime_root / "collective-pattern-ledger" / "graph-projection" / "ugr_graph.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                subject TEXT,
                predicate TEXT,
                object TEXT,
                tenant_scope TEXT,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_claims_subject ON claims(subject);
            CREATE INDEX IF NOT EXISTS idx_claims_tenant ON claims(tenant_scope);
            CREATE INDEX IF NOT EXISTS idx_claims_predicate ON claims(predicate);
            """
        )
        self._conn.commit()

    def rebuild_from_canonical(self, *, max_rows_per_path: int | None = None) -> dict[str, Any]:
        max_rows = int(max_rows_per_path or self.config.get("max_rows_per_path") or 5000)
        paths = discover_claim_paths(self.runtime_root)
        claims = load_claims_from_paths(paths, max_rows_per_path=max_rows)
        self._conn.execute("DELETE FROM claims")
        for row in claims:
            self.on_append(row)
        self._conn.commit()
        count = self._conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        return {
            "backend": self.DRIVER,
            "backend_version": self.BACKEND_VERSION,
            "db_path": str(self.db_path),
            "loaded_claims": len(claims),
            "claim_count": count,
        }

    def on_append(self, record: dict[str, Any]) -> None:
        if str(record.get("record_type") or "claim") != "claim":
            return
        claim_id = str(record.get("claim_id") or "").strip()
        if not claim_id:
            return
        subject = str(record.get("subject") or "")
        predicate = str(record.get("predicate") or "")
        object_value = str(record.get("object") or "")
        tenant_scope = normalize_tenant_id(record.get("tenant_scope") or "global")
        payload = _stable_json(record)
        self._conn.execute(
            """
            INSERT INTO claims (claim_id, subject, predicate, object, tenant_scope, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(claim_id) DO UPDATE SET
                subject=excluded.subject,
                predicate=excluded.predicate,
                object=excluded.object,
                tenant_scope=excluded.tenant_scope,
                payload=excluded.payload
            """,
            (claim_id, subject, predicate, object_value, tenant_scope, payload),
        )

    def _tenant_clause(self, tenant_scope: str | None) -> tuple[str, list[Any]]:
        normalized = normalize_tenant_id(tenant_scope or "global")
        if normalized == "global":
            return "", []
        return " AND tenant_scope IN (?, 'global')", [normalized]

    def query_by_subject(self, subject: str, *, tenant_scope: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        needle = f"%{' '.join(str(subject or '').split()).strip().lower()}%"
        if needle == "%%":
            return []
        tenant_sql, tenant_args = self._tenant_clause(tenant_scope)
        rows = self._conn.execute(
            f"""
            SELECT payload FROM claims
            WHERE lower(subject) LIKE ?{tenant_sql}
            ORDER BY rowid DESC
            LIMIT ?
            """,
            [needle, *tenant_args, int(limit)],
        ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def query_related(self, terms: list[str], *, tenant_scope: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        normalized = [" ".join(str(term).split()).strip().lower() for term in terms if str(term).strip()]
        if not normalized:
            return []
        tenant_sql, tenant_args = self._tenant_clause(tenant_scope)
        clauses = []
        args: list[Any] = []
        for term in normalized:
            like = f"%{term}%"
            clauses.append("(lower(subject) LIKE ? OR lower(predicate) LIKE ? OR lower(object) LIKE ?)")
            args.extend([like, like, like])
        where = " OR ".join(clauses)
        rows = self._conn.execute(
            f"""
            SELECT payload FROM claims
            WHERE ({where}){tenant_sql}
            ORDER BY rowid DESC
            LIMIT ?
            """,
            [*args, *tenant_args, int(limit)],
        ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def stats(self) -> dict[str, Any]:
        count = self._conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        return {
            "backend": self.DRIVER,
            "backend_version": self.BACKEND_VERSION,
            "claim_count": count,
            "db_path": str(self.db_path),
        }

    def close(self) -> None:
        self._conn.close()
