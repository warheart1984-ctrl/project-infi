"""SQLite persistence for hosted Mechanic pilot state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from mechanic.hosted.models import Customer, RepoInstallation, ScanJob, SignoffPolicy


class HostedMechanicStore:
    def __init__(self, *, db_path: str | Path = "", database_url: str = "") -> None:
        self.database_url = database_url
        self.is_postgres = database_url.startswith(("postgres://", "postgresql://"))
        self.db_path = Path(db_path or ".runtime/mechanic-hosted/mechanic_hosted.sqlite3").expanduser().resolve()
        if not self.is_postgres:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> Any:
        if self.is_postgres:
            try:
                import psycopg  # type: ignore[import-not-found]
                from psycopg.rows import dict_row  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError("psycopg is required for Postgres persistence") from exc
            return psycopg.connect(self.database_url, row_factory=dict_row)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            if self.is_postgres:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS customers (
                      customer_id TEXT PRIMARY KEY,
                      payload JSONB NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS installations (
                      installation_id TEXT PRIMARY KEY,
                      customer_id TEXT NOT NULL,
                      payload JSONB NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS scan_jobs (
                      scan_id TEXT PRIMARY KEY,
                      customer_id TEXT NOT NULL,
                      installation_id TEXT NOT NULL,
                      case_id TEXT NOT NULL,
                      status TEXT NOT NULL,
                      payload JSONB NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS evidence_bundles (
                      scan_id TEXT PRIMARY KEY,
                      customer_id TEXT NOT NULL,
                      artifact_dir TEXT NOT NULL,
                      payload JSONB NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS artifact_metadata (
                      scan_id TEXT NOT NULL,
                      name TEXT NOT NULL,
                      path TEXT NOT NULL,
                      sha256 TEXT NOT NULL,
                      PRIMARY KEY (scan_id, name)
                    )
                    """
                )
                conn.commit()
            else:
                conn.executescript(
                    """
                CREATE TABLE IF NOT EXISTS customers (
                  customer_id TEXT PRIMARY KEY,
                  payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS installations (
                  installation_id TEXT PRIMARY KEY,
                  customer_id TEXT NOT NULL,
                  payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS scan_jobs (
                  scan_id TEXT PRIMARY KEY,
                  customer_id TEXT NOT NULL,
                  installation_id TEXT NOT NULL,
                  case_id TEXT NOT NULL,
                  status TEXT NOT NULL,
                  payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_bundles (
                  scan_id TEXT PRIMARY KEY,
                  customer_id TEXT NOT NULL,
                  artifact_dir TEXT NOT NULL,
                  payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifact_metadata (
                  scan_id TEXT NOT NULL,
                  name TEXT NOT NULL,
                  path TEXT NOT NULL,
                  sha256 TEXT NOT NULL,
                  PRIMARY KEY (scan_id, name)
                );
                """
                )

    def save_customer(self, customer: Customer) -> None:
        payload = customer.model_dump()
        self._upsert("customers", "customer_id", customer.customer_id, payload)

    def get_customer(self, customer_id: str) -> Customer | None:
        row = self._get("customers", "customer_id", customer_id)
        if row is None:
            return None
        payload = _payload(row)
        return Customer(**payload)

    def save_installation(self, installation: RepoInstallation) -> None:
        payload = installation.model_dump()
        with self._connect() as conn:
            self._execute(
                conn,
                """
                INSERT INTO installations (installation_id, customer_id, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(installation_id) DO UPDATE SET
                  customer_id=excluded.customer_id,
                  payload=excluded.payload
                """,
                (installation.installation_id, installation.customer_id, json.dumps(payload, sort_keys=True)),
            )
            self._commit(conn)

    def get_installation(self, installation_id: str) -> RepoInstallation | None:
        row = self._get("installations", "installation_id", installation_id)
        if row is None:
            return None
        payload = _payload(row)
        policy_payload = payload.pop("policy_profile", {})
        payload["policy_profile"] = SignoffPolicy(**policy_payload)
        return RepoInstallation(**payload)

    def save_scan_job(self, job: ScanJob) -> None:
        payload = job.model_dump()
        with self._connect() as conn:
            self._execute(
                conn,
                """
                INSERT INTO scan_jobs (scan_id, customer_id, installation_id, case_id, status, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(scan_id) DO UPDATE SET
                  customer_id=excluded.customer_id,
                  installation_id=excluded.installation_id,
                  case_id=excluded.case_id,
                  status=excluded.status,
                  payload=excluded.payload
                """,
                (
                    job.scan_id,
                    job.customer_id,
                    job.installation_id,
                    job.case_id,
                    job.status,
                    json.dumps(payload, sort_keys=True),
                ),
            )
            self._commit(conn)

    def get_scan_job(self, scan_id: str) -> ScanJob | None:
        row = self._get("scan_jobs", "scan_id", scan_id)
        if row is None:
            return None
        payload = _payload(row)
        payload.pop("sla_deadline_utc", None)
        return ScanJob(**payload)

    def save_evidence_bundle(self, scan_id: str, customer_id: str, bundle: dict[str, Any]) -> None:
        artifact_dir = str(bundle.get("artifact_dir") or "")
        with self._connect() as conn:
            self._execute(
                conn,
                """
                INSERT INTO evidence_bundles (scan_id, customer_id, artifact_dir, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(scan_id) DO UPDATE SET
                  customer_id=excluded.customer_id,
                  artifact_dir=excluded.artifact_dir,
                  payload=excluded.payload
                """,
                (scan_id, customer_id, artifact_dir, json.dumps(bundle, sort_keys=True)),
            )
            for name, meta in (bundle.get("artifacts") or {}).items():
                self._execute(
                    conn,
                    """
                    INSERT INTO artifact_metadata (scan_id, name, path, sha256)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(scan_id, name) DO UPDATE SET
                      path=excluded.path,
                      sha256=excluded.sha256
                    """,
                    (scan_id, str(name), str(meta.get("path") or ""), str(meta.get("sha256") or "")),
                )
            self._commit(conn)

    def get_evidence_bundle(self, scan_id: str) -> dict[str, Any] | None:
        row = self._get("evidence_bundles", "scan_id", scan_id)
        return _payload(row) if row is not None else None

    def _upsert(self, table: str, key: str, key_value: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            self._execute(
                conn,
                f"""
                INSERT INTO {table} ({key}, payload)
                VALUES (?, ?)
                ON CONFLICT({key}) DO UPDATE SET payload=excluded.payload
                """,
                (key_value, json.dumps(payload, sort_keys=True)),
            )
            self._commit(conn)

    def _get(self, table: str, key: str, key_value: str) -> Any:
        with self._connect() as conn:
            cursor = self._execute(conn, f"SELECT * FROM {table} WHERE {key} = ?", (key_value,))
            return cursor.fetchone()

    def _execute(self, conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
        if self.is_postgres:
            from psycopg.types.json import Jsonb  # type: ignore[import-not-found]

            sql = sql.replace("?", "%s")
            sql = sql.replace("ON CONFLICT(customer_id) DO UPDATE SET payload=excluded.payload", "ON CONFLICT(customer_id) DO UPDATE SET payload=EXCLUDED.payload")
            sql = sql.replace("ON CONFLICT(installation_id) DO UPDATE SET", "ON CONFLICT(installation_id) DO UPDATE SET")
            sql = sql.replace("excluded.", "EXCLUDED.")
            converted = tuple(_maybe_jsonb(item) for item in params)
            return conn.execute(sql, converted)
        return conn.execute(sql, params)

    def _commit(self, conn: Any) -> None:
        if self.is_postgres:
            conn.commit()


def _payload(row: Any) -> dict[str, Any]:
    value = row["payload"]
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def _maybe_jsonb(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "[{":
        return value
    try:
        import json as _json
        from psycopg.types.json import Jsonb  # type: ignore[import-not-found]

        return Jsonb(_json.loads(text))
    except (ValueError, TypeError):
        return value
