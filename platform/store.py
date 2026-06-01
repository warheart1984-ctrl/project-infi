"""Platform persistence (SQLite dev / Postgres SaaS)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from datetime import datetime

from src.datetime_compat import UTC

from platform.auth.api_keys import hash_api_key
from platform.common import new_id, normalize_org_role, scopes_for_roles


class PlatformStore:
    def __init__(self, *, db_path: str | Path = "", database_url: str = "") -> None:
        self.database_url = database_url
        self.is_postgres = database_url.startswith(("postgres://", "postgresql://"))
        self.db_path = Path(db_path or ".runtime/platform/platform.sqlite3").expanduser().resolve()
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
                    "CREATE TABLE IF NOT EXISTS orgs (org_id TEXT PRIMARY KEY, payload JSONB NOT NULL)"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS principals (principal_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, payload JSONB NOT NULL)"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS api_keys (api_key_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, principal_id TEXT NOT NULL, key_hash TEXT NOT NULL, payload JSONB NOT NULL)"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS platform_jobs (job_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, payload JSONB NOT NULL)"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS artifact_refs (ref_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, payload JSONB NOT NULL)"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS audit_rows (id SERIAL PRIMARY KEY, org_id TEXT NOT NULL, payload JSONB NOT NULL)"
                )
                for stmt in (
                    "CREATE TABLE IF NOT EXISTS role_bindings (binding_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, principal_id TEXT NOT NULL, payload JSONB NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS invites (invite_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, token_hash TEXT NOT NULL, payload JSONB NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS usage_daily (org_id TEXT NOT NULL, day TEXT NOT NULL, payload JSONB NOT NULL, PRIMARY KEY (org_id, day))",
                    "CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, payload JSONB NOT NULL)",
                ):
                    conn.execute(stmt)
                conn.commit()
            else:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS orgs (
                      org_id TEXT PRIMARY KEY,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS principals (
                      principal_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS api_keys (
                      api_key_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      principal_id TEXT NOT NULL,
                      key_hash TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS platform_jobs (
                      job_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS artifact_refs (
                      ref_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS audit_rows (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS role_bindings (
                      binding_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      principal_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS invites (
                      invite_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      token_hash TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS usage_daily (
                      org_id TEXT NOT NULL,
                      day TEXT NOT NULL,
                      payload TEXT NOT NULL,
                      PRIMARY KEY (org_id, day)
                    );
                    CREATE TABLE IF NOT EXISTS sessions (
                      session_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS billing_periods (
                      org_id TEXT NOT NULL,
                      period TEXT NOT NULL,
                      payload TEXT NOT NULL,
                      PRIMARY KEY (org_id, period)
                    );
                    CREATE TABLE IF NOT EXISTS org_policy_rules (
                      rule_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS workflows (
                      workflow_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS operator_presence (
                      org_id TEXT NOT NULL,
                      principal_id TEXT NOT NULL,
                      payload TEXT NOT NULL,
                      PRIMARY KEY (org_id, principal_id)
                    );
                    CREATE TABLE IF NOT EXISTS job_assignments (
                      job_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS mesh_events (
                      event_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS on_call_schedules (
                      rotation_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS handoff_bundles (
                      bundle_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS workflow_listings (
                      listing_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS proof_attestations (
                      attestation_id TEXT PRIMARY KEY,
                      job_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS proof_runners (
                      runner_id TEXT PRIMARY KEY,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS webhook_subscriptions (
                      subscription_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS webhook_deliveries (
                      delivery_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS listing_reviews (
                      review_id TEXT PRIMARY KEY,
                      listing_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_jobs_org ON platform_jobs(org_id);
                    CREATE INDEX IF NOT EXISTS idx_artifacts_org_job ON artifact_refs(org_id);
                    CREATE TABLE IF NOT EXISTS platform_ledger (
                      entry_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS proof_witnesses (
                      witness_id TEXT PRIMARY KEY,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS platform_peers (
                      peer_id TEXT PRIMARY KEY,
                      payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS autopilot_runs (
                      run_id TEXT PRIMARY KEY,
                      org_id TEXT NOT NULL,
                      payload TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_mesh_events_org ON mesh_events(org_id);
                    CREATE INDEX IF NOT EXISTS idx_ledger_org ON platform_ledger(org_id);
                    """
                )

    @staticmethod
    def _dump(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True)

    @staticmethod
    def _load(raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        return json.loads(str(raw))

    def upsert_org(self, payload: dict[str, Any]) -> dict[str, Any]:
        org_id = str(payload["org_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO orgs (org_id, payload) VALUES (?, ?) ON CONFLICT(org_id) DO UPDATE SET payload=excluded.payload",
                (org_id, self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_org(self, org_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM orgs WHERE org_id = ?", (org_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def upsert_principal(self, payload: dict[str, Any]) -> dict[str, Any]:
        pid = str(payload["principal_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO principals (principal_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(principal_id) DO UPDATE SET org_id=excluded.org_id, payload=excluded.payload",
                (pid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def create_api_key(
        self,
        *,
        org_id: str,
        principal_id: str,
        roles: list[str],
        display_name: str = "",
        scopes: list[str] | None = None,
        raw_key: str | None = None,
    ) -> tuple[str, str, dict[str, Any]]:
        import secrets

        key = raw_key or secrets.token_urlsafe(32)
        api_key_id = new_id("pkey")
        norm_roles = [normalize_org_role(r) for r in roles]
        record = {
            "api_key_id": api_key_id,
            "org_id": org_id,
            "principal_id": principal_id,
            "roles": norm_roles,
            "scopes": scopes or scopes_for_roles(norm_roles),
            "display_name": display_name,
            "key_hash": hash_api_key(key),
        }
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO api_keys (api_key_id, org_id, principal_id, key_hash, payload) VALUES (?, ?, ?, ?, ?)",
                (api_key_id, org_id, principal_id, record["key_hash"], self._dump(record)),
            )
            conn.commit()
        return key, api_key_id, record

    def resolve_api_key(self, provided: str) -> dict[str, Any] | None:
        digest = hash_api_key(provided)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM api_keys WHERE key_hash = ?",
                (digest,),
            ).fetchone()
        if not row:
            if digest and provided:
                pass
            return None
        key_rec = self._load(row["payload"])
        principal = self.get_principal(str(key_rec["principal_id"]))
        if not principal:
            return None
        roles = key_rec.get("roles") or principal.get("roles") or ["read_only"]
        bindings = self.list_role_bindings(org_id=str(key_rec["org_id"]), principal_id=str(key_rec["principal_id"]))
        if bindings:
            roles = [str(b["role"]) for b in bindings]
        scopes = key_rec.get("scopes") or scopes_for_roles([normalize_org_role(str(r)) for r in roles])
        return {
            "api_key_id": key_rec["api_key_id"],
            "org_id": key_rec["org_id"],
            "principal_id": key_rec["principal_id"],
            "roles": roles,
            "scopes": scopes,
            "display_name": key_rec.get("display_name") or principal.get("display_name", ""),
            "principal_kind": principal.get("principal_kind", "service_account"),
        }

    def get_principal(self, principal_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM principals WHERE principal_id = ?", (principal_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def upsert_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = str(payload["job_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO platform_jobs (job_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(job_id) DO UPDATE SET org_id=excluded.org_id, payload=excluded.payload",
                (job_id, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM platform_jobs WHERE job_id = ?", (job_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def list_orgs(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM orgs").fetchall()
        return [self._load(r["payload"]) for r in rows]

    def list_principals(self, *, org_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM principals WHERE org_id = ?", (org_id,)).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_role_binding(
        self,
        *,
        org_id: str,
        principal_id: str,
        role: str,
        granted_by: str,
    ) -> dict[str, Any]:
        binding_id = f"{org_id}:{principal_id}"
        payload = {
            "binding_version": "platform.platform_role_binding.v1",
            "binding_id": binding_id,
            "org_id": org_id,
            "principal_id": principal_id,
            "role": normalize_org_role(role),
            "granted_by": granted_by,
            "granted_at": datetime.now(UTC).isoformat(),
        }
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO role_bindings (binding_id, org_id, principal_id, payload) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(binding_id) DO UPDATE SET payload=excluded.payload",
                (binding_id, org_id, principal_id, self._dump(payload)),
            )
            conn.commit()
        principal = self.get_principal(principal_id)
        if principal:
            principal["roles"] = [payload["role"]]
            self.upsert_principal(principal)
        return payload

    def list_role_bindings(self, *, org_id: str, principal_id: str = "") -> list[dict[str, Any]]:
        with self._connect() as conn:
            if principal_id:
                rows = conn.execute(
                    "SELECT payload FROM role_bindings WHERE org_id = ? AND principal_id = ?",
                    (org_id, principal_id),
                ).fetchall()
            else:
                rows = conn.execute("SELECT payload FROM role_bindings WHERE org_id = ?", (org_id,)).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def create_invite(
        self,
        *,
        org_id: str,
        email: str,
        role: str,
        token: str,
        expires_at: str,
        created_by: str,
    ) -> dict[str, Any]:
        invite_id = new_id("inv")
        payload = {
            "invite_id": invite_id,
            "org_id": org_id,
            "email": email,
            "role": normalize_org_role(role),
            "token_hash": hash_api_key(token),
            "expires_at": expires_at,
            "created_by": created_by,
            "accepted_at": "",
        }
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO invites (invite_id, org_id, token_hash, payload) VALUES (?, ?, ?, ?)",
                (invite_id, org_id, payload["token_hash"], self._dump(payload)),
            )
            conn.commit()
        return {**payload, "invite_token": token}

    def accept_invite(
        self,
        *,
        token: str,
        principal_id: str,
        display_name: str = "",
    ) -> dict[str, Any] | None:
        digest = hash_api_key(token)
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM invites WHERE token_hash = ?", (digest,)).fetchone()
        if not row:
            return None
        invite = self._load(row["payload"])
        if invite.get("accepted_at"):
            return None
        org_id = str(invite["org_id"])
        self.upsert_principal(
            {
                "principal_id": principal_id,
                "org_id": org_id,
                "roles": [invite["role"]],
                "principal_kind": "human",
                "display_name": display_name,
            }
        )
        self.upsert_role_binding(
            org_id=org_id,
            principal_id=principal_id,
            role=str(invite["role"]),
            granted_by=str(invite.get("created_by") or "invite"),
        )
        raw, api_key_id, _ = self.create_api_key(
            org_id=org_id,
            principal_id=principal_id,
            roles=[str(invite["role"])],
            display_name=display_name,
        )
        invite["accepted_at"] = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE invites SET payload = ? WHERE invite_id = ?",
                (self._dump(invite), str(invite["invite_id"])),
            )
            conn.commit()
        return {"org_id": org_id, "principal_id": principal_id, "api_key": raw, "api_key_id": api_key_id}

    def record_usage(self, *, org_id: str, event: dict[str, Any]) -> None:
        day = str(event.get("day") or datetime.now(UTC).date().isoformat())
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM usage_daily WHERE org_id = ? AND day = ?",
                (org_id, day),
            ).fetchone()
        if row:
            payload = self._load(row["payload"])
        else:
            payload = {
                "org_id": org_id,
                "day": day,
                "jobs_count": 0,
                "mechanic_jobs": 0,
                "slingshot_jobs": 0,
                "artifacts_count": 0,
                "storage_bytes": 0,
                "estimated_cost": 0.0,
            }
        for key in (
            "jobs_count",
            "mechanic_jobs",
            "slingshot_jobs",
            "artifacts_count",
            "marketplace_installs",
            "workflow_runs_from_listing",
        ):
            if key in event:
                payload[key] = int(payload.get(key, 0)) + int(event[key])
        if "listing_installs_by_id" in event:
            meta = dict(payload.get("metadata") or {})
            by_id = dict(meta.get("listing_installs_by_id") or {})
            for lid, cnt in (event.get("listing_installs_by_id") or {}).items():
                by_id[str(lid)] = int(by_id.get(str(lid), 0)) + int(cnt)
            meta["listing_installs_by_id"] = by_id
            payload["metadata"] = meta
        if "storage_bytes" in event:
            payload["storage_bytes"] = int(payload.get("storage_bytes", 0)) + int(event["storage_bytes"])
        if "estimated_cost" in event:
            payload["estimated_cost"] = float(payload.get("estimated_cost", 0)) + float(event["estimated_cost"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO usage_daily (org_id, day, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(org_id, day) DO UPDATE SET payload=excluded.payload",
                (org_id, day, self._dump(payload)),
            )
            conn.commit()

    def list_usage(self, *, org_id: str, day_from: str = "", day_to: str = "") -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM usage_daily WHERE org_id = ?", (org_id,)).fetchall()
        items = [self._load(r["payload"]) for r in rows]
        if day_from:
            items = [i for i in items if str(i.get("day", "")) >= day_from]
        if day_to:
            items = [i for i in items if str(i.get("day", "")) <= day_to]
        return sorted(items, key=lambda i: str(i.get("day", "")))

    def list_jobs(
        self,
        *,
        org_id: str,
        subsystem: str = "",
        status: str = "",
        correlation_id: str = "",
        job_type: str = "",
        proof_status: str = "",
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM platform_jobs WHERE org_id = ?", (org_id,)).fetchall()
        jobs = [self._load(r["payload"]) for r in rows]
        if subsystem:
            jobs = [j for j in jobs if j.get("subsystem") == subsystem]
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        if correlation_id:
            jobs = [j for j in jobs if j.get("correlation_id") == correlation_id]
        if job_type:
            jobs = [j for j in jobs if j.get("job_type") == job_type]
        if proof_status:
            jobs = [j for j in jobs if j.get("proof_status") == proof_status]
        return sorted(jobs, key=lambda j: str(j.get("created_at", "")), reverse=True)

    def upsert_artifact_ref(self, payload: dict[str, Any]) -> dict[str, Any]:
        ref_id = str(payload["ref_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO artifact_refs (ref_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(ref_id) DO UPDATE SET org_id=excluded.org_id, payload=excluded.payload",
                (ref_id, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_artifact_ref(self, ref_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM artifact_refs WHERE ref_id = ?", (ref_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def list_artifact_refs(
        self,
        *,
        org_id: str,
        subsystem: str = "",
        correlation_id: str = "",
        job_id: str = "",
        artifact_type: str = "",
        visibility: str = "",
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM artifact_refs WHERE org_id = ?", (org_id,)).fetchall()
        refs = [self._load(r["payload"]) for r in rows]
        if subsystem:
            refs = [r for r in refs if r.get("subsystem") == subsystem]
        if correlation_id:
            refs = [r for r in refs if r.get("correlation_id") == correlation_id]
        if job_id:
            refs = [r for r in refs if r.get("job_id") == job_id]
        if artifact_type:
            refs = [r for r in refs if r.get("artifact_type") == artifact_type]
        if visibility:
            refs = [r for r in refs if (r.get("visibility") or (r.get("acl") or {}).get("visibility")) == visibility]
        return sorted(refs, key=lambda r: str(r.get("registered_at", "")), reverse=True)

    def append_audit_row(self, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_rows (org_id, payload) VALUES (?, ?)",
                (str(payload.get("org_id", "")), self._dump(payload)),
            )
            conn.commit()

    def list_audit(self, *, org_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM audit_rows WHERE org_id = ? ORDER BY id DESC LIMIT ?",
                (org_id, limit),
            ).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_billing_period(self, payload: dict[str, Any]) -> dict[str, Any]:
        org_id = str(payload["org_id"])
        period = str(payload.get("period") or "")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO billing_periods (org_id, period, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(org_id, period) DO UPDATE SET payload=excluded.payload",
                (org_id, period, self._dump(payload)),
            )
            conn.commit()
        return payload

    def list_billing_periods(self, *, org_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM billing_periods WHERE org_id = ?",
                (org_id,),
            ).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_policy_rule(self, payload: dict[str, Any]) -> dict[str, Any]:
        rule_id = str(payload["rule_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO org_policy_rules (rule_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(rule_id) DO UPDATE SET payload=excluded.payload",
                (rule_id, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def list_policy_rules(self, *, org_id: str, enabled_only: bool = True) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM org_policy_rules WHERE org_id = ?",
                (org_id,),
            ).fetchall()
        rules = [self._load(r["payload"]) for r in rows]
        if enabled_only:
            rules = [r for r in rules if r.get("enabled", True)]
        return rules

    def delete_policy_rules(self, *, org_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM org_policy_rules WHERE org_id = ?", (org_id,))
            conn.commit()

    def resolve_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def upsert_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        wid = str(payload["workflow_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO workflows (workflow_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(workflow_id) DO UPDATE SET org_id=excluded.org_id, payload=excluded.payload",
                (wid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM workflows WHERE workflow_id = ?", (workflow_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def list_workflows(self, *, org_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM workflows WHERE org_id = ?", (org_id,)).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_presence(self, payload: dict[str, Any]) -> dict[str, Any]:
        org_id = str(payload["org_id"])
        principal_id = str(payload["principal_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO operator_presence (org_id, principal_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(org_id, principal_id) DO UPDATE SET payload=excluded.payload",
                (org_id, principal_id, self._dump(payload)),
            )
            conn.commit()
        return payload

    def list_presence(self, *, org_id: str, max_age_seconds: int = 300) -> list[dict[str, Any]]:
        from datetime import datetime, timedelta

        from src.datetime_compat import UTC

        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_seconds)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM operator_presence WHERE org_id = ?",
                (org_id,),
            ).fetchall()
        out = []
        for r in rows:
            p = self._load(r["payload"])
            if str(p.get("status")) == "online":
                try:
                    seen = datetime.fromisoformat(str(p.get("last_seen", "")).replace("Z", "+00:00"))
                    if seen >= cutoff:
                        out.append(p)
                except ValueError:
                    out.append(p)
        return out

    def upsert_assignment(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = str(payload["job_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO job_assignments (job_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(job_id) DO UPDATE SET payload=excluded.payload",
                (job_id, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_assignment(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM job_assignments WHERE job_id = ?", (job_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def delete_assignment(self, job_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM job_assignments WHERE job_id = ?", (job_id,))
            conn.commit()

    def append_mesh_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        eid = str(payload["event_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO mesh_events (event_id, org_id, payload) VALUES (?, ?, ?)",
                (eid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def list_mesh_events(self, *, org_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM mesh_events WHERE org_id = ? ORDER BY event_id DESC LIMIT ?",
                (org_id, limit),
            ).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_on_call(self, payload: dict[str, Any]) -> dict[str, Any]:
        rid = str(payload["rotation_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO on_call_schedules (rotation_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(rotation_id) DO UPDATE SET payload=excluded.payload",
                (rid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_on_call(self, org_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM on_call_schedules WHERE org_id = ? ORDER BY rotation_id DESC LIMIT 1",
                (org_id,),
            ).fetchone()
        return self._load(row["payload"]) if row else None

    def upsert_handoff(self, payload: dict[str, Any]) -> dict[str, Any]:
        bid = str(payload["bundle_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO handoff_bundles (bundle_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(bundle_id) DO UPDATE SET payload=excluded.payload",
                (bid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_handoff(self, bundle_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM handoff_bundles WHERE bundle_id = ?", (bundle_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def upsert_listing(self, payload: dict[str, Any]) -> dict[str, Any]:
        lid = str(payload["listing_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO workflow_listings (listing_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(listing_id) DO UPDATE SET payload=excluded.payload",
                (lid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_listing(self, listing_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM workflow_listings WHERE listing_id = ?", (listing_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def list_listings(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM workflow_listings").fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_attestation(self, payload: dict[str, Any]) -> dict[str, Any]:
        aid = str(payload["attestation_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO proof_attestations (attestation_id, job_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(attestation_id) DO UPDATE SET payload=excluded.payload",
                (aid, str(payload["job_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def list_attestations(self, *, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM proof_attestations WHERE job_id = ?",
                (job_id,),
            ).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_proof_runner(self, payload: dict[str, Any]) -> dict[str, Any]:
        rid = str(payload["runner_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO proof_runners (runner_id, payload) VALUES (?, ?) "
                "ON CONFLICT(runner_id) DO UPDATE SET payload=excluded.payload",
                (rid, self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_proof_runner(self, runner_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM proof_runners WHERE runner_id = ?", (runner_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def list_proof_runners(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM proof_runners").fetchall()
        return [self._load(r["payload"]) for r in rows]

    def list_orgs_by_tenant(self, ugr_tenant_id: str) -> list[dict[str, Any]]:
        return [o for o in self.list_orgs() if str(o.get("ugr_tenant_id") or "") == ugr_tenant_id]

    def upsert_webhook_subscription(self, payload: dict[str, Any]) -> dict[str, Any]:
        sid = str(payload["subscription_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO webhook_subscriptions (subscription_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(subscription_id) DO UPDATE SET payload=excluded.payload",
                (sid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_webhook_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM webhook_subscriptions WHERE subscription_id = ?",
                (subscription_id,),
            ).fetchone()
        return self._load(row["payload"]) if row else None

    def list_webhook_subscriptions(self, *, org_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM webhook_subscriptions WHERE org_id = ?",
                (org_id,),
            ).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def delete_webhook_subscription(self, subscription_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM webhook_subscriptions WHERE subscription_id = ?", (subscription_id,))
            conn.commit()

    def record_webhook_delivery(self, payload: dict[str, Any]) -> dict[str, Any]:
        did = str(payload["delivery_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO webhook_deliveries (delivery_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(delivery_id) DO UPDATE SET payload=excluded.payload",
                (did, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def count_webhook_failures(self, *, org_id: str) -> int:
        n = 0
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM webhook_deliveries WHERE org_id = ?",
                (org_id,),
            ).fetchall()
        for r in rows:
            p = self._load(r["payload"])
            if p.get("status") == "failed":
                n += 1
        return n

    def upsert_listing_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        rid = str(payload["review_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO listing_reviews (review_id, listing_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(review_id) DO UPDATE SET payload=excluded.payload",
                (rid, str(payload["listing_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def list_listing_reviews(self, *, listing_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM listing_reviews WHERE listing_id = ?",
                (listing_id,),
            ).fetchall()
        return [self._load(r["payload"]) for r in rows]

    def list_mesh_events_after(
        self,
        *,
        org_id: str,
        cursor: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        events = self.list_mesh_events(org_id=org_id, limit=500)
        if cursor:
            found = False
            filtered: list[dict[str, Any]] = []
            for ev in events:
                if found:
                    filtered.append(ev)
                elif str(ev.get("event_id")) == cursor:
                    found = True
            events = filtered
        return events[:limit]

    def compact_mesh_events(self, *, org_id: str, before_iso: str) -> int:
        removed = 0
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_id, payload FROM mesh_events WHERE org_id = ?",
                (org_id,),
            ).fetchall()
            for row in rows:
                ev = self._load(row["payload"])
                if str(ev.get("created_at") or "") < before_iso:
                    conn.execute("DELETE FROM mesh_events WHERE event_id = ?", (str(row["event_id"]),))
                    removed += 1
            conn.commit()
        return removed

    def append_ledger_entry(self, payload: dict[str, Any]) -> dict[str, Any]:
        eid = str(payload["entry_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO platform_ledger (entry_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(entry_id) DO UPDATE SET payload=excluded.payload",
                (eid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_ledger_tail_hash(self, *, org_id: str) -> str:
        entries = self.list_ledger_entries(org_id=org_id, limit=10000)
        if not entries:
            return ""
        return str(entries[-1].get("entry_hash") or "")

    def list_ledger_entries(
        self,
        *,
        org_id: str,
        kind: str = "",
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM platform_ledger WHERE org_id = ? ORDER BY rowid ASC",
                (org_id,),
            ).fetchall()
        items = [self._load(r["payload"]) for r in rows]
        if kind:
            items = [e for e in items if e.get("kind") == kind]
        return items[:limit]

    def upsert_proof_witness(self, payload: dict[str, Any]) -> dict[str, Any]:
        wid = str(payload["witness_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO proof_witnesses (witness_id, payload) VALUES (?, ?) "
                "ON CONFLICT(witness_id) DO UPDATE SET payload=excluded.payload",
                (wid, self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_proof_witness(self, witness_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM proof_witnesses WHERE witness_id = ?",
                (witness_id,),
            ).fetchone()
        return self._load(row["payload"]) if row else None

    def list_proof_witnesses(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM proof_witnesses").fetchall()
        return [self._load(r["payload"]) for r in rows]

    def upsert_platform_peer(self, payload: dict[str, Any]) -> dict[str, Any]:
        pid = str(payload["peer_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO platform_peers (peer_id, payload) VALUES (?, ?) "
                "ON CONFLICT(peer_id) DO UPDATE SET payload=excluded.payload",
                (pid, self._dump(payload)),
            )
            conn.commit()
        return payload

    def get_platform_peer(self, peer_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM platform_peers WHERE peer_id = ?", (peer_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def list_platform_peers(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM platform_peers").fetchall()
        return [self._load(r["payload"]) for r in rows]

    def append_autopilot_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        rid = str(payload["run_id"])
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO autopilot_runs (run_id, org_id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(run_id) DO UPDATE SET payload=excluded.payload",
                (rid, str(payload["org_id"]), self._dump(payload)),
            )
            conn.commit()
        return payload
