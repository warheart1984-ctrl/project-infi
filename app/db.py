from __future__ import annotations
import sqlite3
import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from app.config import DB_PATH
from src.cisiv import normalize_cisiv_stage


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    existing = {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name in existing:
        return
    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


_UNSET = object()
ACTIVE_WORKFLOW_RUN_STATUSES = ("queued", "running", "awaiting_approval", "stale", "recovering")

def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            goal TEXT NOT NULL,
            status TEXT NOT NULL,
            result_json TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS job_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS response_cache (
            cache_key TEXT PRIMARY KEY,
            response TEXT NOT NULL,
            used_tool TEXT,
            tool_result TEXT,
            route TEXT,
            created_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            nodes_json TEXT NOT NULL,
            edges_json TEXT NOT NULL,
            config_json TEXT NOT NULL,
            cisiv_stage TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            status TEXT NOT NULL,
            output_json TEXT NOT NULL,
            cisiv_stage TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            lease_owner TEXT,
            lease_expires_at TEXT,
            last_heartbeat_at TEXT,
            recovery_state TEXT,
            recovery_attempts INTEGER NOT NULL DEFAULT 0,
            stale_reason TEXT,
            FOREIGN KEY(workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS workflow_approvals (
            id TEXT PRIMARY KEY,
            workflow_run_id TEXT NOT NULL,
            workflow_id TEXT NOT NULL,
            step_id TEXT NOT NULL,
            step_label TEXT NOT NULL,
            step_type TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            payload_json TEXT NOT NULL,
            cisiv_stage TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(workflow_run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE,
            FOREIGN KEY(workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS app_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            onboarding_done INTEGER NOT NULL DEFAULT 0,
            goal TEXT,
            tools_json TEXT NOT NULL DEFAULT '[]',
            cisiv_stage TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        _ensure_column(conn, "workflows", "cisiv_stage", "TEXT")
        _ensure_column(conn, "workflow_runs", "cisiv_stage", "TEXT")
        _ensure_column(conn, "workflow_approvals", "cisiv_stage", "TEXT")
        _ensure_column(conn, "app_profile", "cisiv_stage", "TEXT")
        _ensure_column(conn, "workflow_runs", "lease_owner", "TEXT")
        _ensure_column(conn, "workflow_runs", "lease_expires_at", "TEXT")
        _ensure_column(conn, "workflow_runs", "last_heartbeat_at", "TEXT")
        _ensure_column(conn, "workflow_runs", "recovery_state", "TEXT")
        _ensure_column(conn, "workflow_runs", "recovery_attempts", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "workflow_runs", "stale_reason", "TEXT")

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def offset_iso(seconds: int) -> str:
    return (
        datetime.now(timezone.utc) + timedelta(seconds=seconds)
    ).isoformat().replace("+00:00", "Z")

def save_message(session_id: str, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now_iso())
        )

def load_recent_messages(session_id: str, limit: int = 20) -> list[dict[str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
    rows = list(reversed(rows))
    return [{"role": role, "content": content} for role, content in rows]

def load_all_messages(session_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        ).fetchall()
    return [{"role": r, "content": c, "created_at": t} for r, c, t in rows]

def export_session(session_id: str) -> dict:
    return {"session_id": session_id, "messages": load_all_messages(session_id)}

def create_job(job_id: str, session_id: str, goal: str) -> None:
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO jobs (job_id, session_id, goal, status, result_json, error, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, session_id, goal, "queued", None, None, ts, ts)
        )

def update_job(job_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, result_json = ?, error = ?, updated_at = ? WHERE job_id = ?",
            (status, json.dumps(result) if result is not None else None, error, now_iso(), job_id)
        )

def get_job(job_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT job_id, session_id, goal, status, result_json, error, created_at, updated_at FROM jobs WHERE job_id = ?",
            (job_id,)
        ).fetchone()
    if not row:
        return None
    return {
        "job_id": row[0],
        "session_id": row[1],
        "goal": row[2],
        "status": row[3],
        "result": json.loads(row[4]) if row[4] else None,
        "error": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }

def log_event(event_type: str, payload: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO events (event_type, payload_json, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload), now_iso())
        )

def add_job_event(job_id: str, event_type: str, payload: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO job_events (job_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (job_id, event_type, json.dumps(payload), now_iso())
        )

def get_job_events_since(job_id: str, last_id: int = 0) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, event_type, payload_json, created_at FROM job_events WHERE job_id = ? AND id > ? ORDER BY id ASC",
            (job_id, last_id)
        ).fetchall()
    return [
        {"id": row[0], "event_type": row[1], "payload": json.loads(row[2]), "created_at": row[3]}
        for row in rows
    ]

def get_cached_response(cache_key: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT response, used_tool, tool_result, route, created_at FROM response_cache WHERE cache_key = ?",
            (cache_key,)
        ).fetchone()
    if not row:
        return None
    return {
        "response": row[0],
        "used_tool": row[1],
        "tool_result": row[2],
        "route": row[3],
        "created_at": row[4],
    }

def set_cached_response(cache_key: str, response: str, used_tool: str | None, tool_result: str | None, route: str | None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO response_cache (cache_key, response, used_tool, tool_result, route, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (cache_key, response, used_tool, tool_result, route, now_iso())
        )

def _json_loads(raw: str | None, fallback):
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback

def _serialize_workflow_row(row) -> dict | None:
    if not row:
        return None
    cisiv_stage = normalize_cisiv_stage(row[8], default="structure")
    return {
        "id": row[0],
        "name": row[1],
        "active": bool(row[2]),
        "nodes": _json_loads(row[3], []),
        "edges": _json_loads(row[4], []),
        "config": _json_loads(row[5], {}),
        "created_at": row[6],
        "updated_at": row[7],
        "cisiv_stage": cisiv_stage,
    }

def create_workflow(
    name: str,
    nodes: list,
    edges: list,
    config: dict,
    active: bool = True,
    cisiv_stage: str | None = None,
) -> dict:
    workflow_id = str(uuid.uuid4())
    ts = now_iso()
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="structure")
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO workflows (
                id, name, active, nodes_json, edges_json, config_json, cisiv_stage, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workflow_id,
                name,
                1 if active else 0,
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps(config),
                normalized_cisiv_stage,
                ts,
                ts,
            ),
        )
    return get_workflow(workflow_id)

def update_workflow(
    workflow_id: str,
    name: str,
    nodes: list,
    edges: list,
    config: dict,
    cisiv_stage: str | None = None,
) -> dict | None:
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="structure")
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE workflows
            SET name = ?, nodes_json = ?, edges_json = ?, config_json = ?, cisiv_stage = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name,
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps(config),
                normalized_cisiv_stage,
                now_iso(),
                workflow_id,
            ),
        )
    return get_workflow(workflow_id)

def get_workflow(workflow_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, active, nodes_json, edges_json, config_json, created_at, updated_at, cisiv_stage
            FROM workflows
            WHERE id = ?
            """,
            (workflow_id,),
        ).fetchone()
    return _serialize_workflow_row(row)

def get_latest_workflow() -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, active, nodes_json, edges_json, config_json, created_at, updated_at, cisiv_stage
            FROM workflows
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ).fetchone()
    return _serialize_workflow_row(row)

def list_workflows(limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, active, nodes_json, edges_json, config_json, created_at, updated_at, cisiv_stage
            FROM workflows
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_serialize_workflow_row(row) for row in rows]

def create_workflow_run(
    workflow_id: str,
    status: str,
    output: dict | None = None,
    cisiv_stage: str | None = None,
) -> dict | None:
    run_id = str(uuid.uuid4())
    ts = now_iso()
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="implementation")
    normalized_output = dict(output or {})
    normalized_output["cisiv_stage"] = normalize_cisiv_stage(
        normalized_output.get("cisiv_stage"),
        default=normalized_cisiv_stage,
    )
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO workflow_runs (
                id, workflow_id, status, output_json, cisiv_stage, created_at, updated_at,
                lease_owner, lease_expires_at, last_heartbeat_at,
                recovery_state, recovery_attempts, stale_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                workflow_id,
                status,
                json.dumps(normalized_output),
                normalized_output["cisiv_stage"],
                ts,
                ts,
                None,
                None,
                None,
                None,
                0,
                None,
            ),
        )
    return get_workflow_run(run_id)


def _append_run_ledger(output: dict, event_type: str, message: str, **extra) -> dict:
    ledger = list(output.get("ledger") or [])
    cisiv_stage = normalize_cisiv_stage(
        extra.pop("cisiv_stage", None) or output.get("cisiv_stage"),
        default="implementation",
    )
    ledger.append(
        {
            "type": event_type,
            "message": message,
            "at": now_iso(),
            "cisiv_stage": cisiv_stage,
            **extra,
        }
    )
    output["ledger"] = ledger[-25:]
    output["cisiv_stage"] = cisiv_stage
    return output


def update_workflow_run(
    workflow_run_id: str,
    status: str | None = None,
    output: dict | None = None,
    expected_statuses: list[str] | None = None,
    expected_lease_owner: str | None = None,
    lease_owner=_UNSET,
    lease_expires_at=_UNSET,
    last_heartbeat_at=_UNSET,
    clear_lease: bool = False,
    recovery_state=_UNSET,
    recovery_attempts=_UNSET,
    stale_reason=_UNSET,
    cisiv_stage=_UNSET,
) -> dict | None:
    current = get_workflow_run(workflow_run_id)
    if not current:
        return None

    next_status = status or current["status"]
    next_cisiv_stage = (
        current.get("cisiv_stage")
        if cisiv_stage is _UNSET
        else normalize_cisiv_stage(cisiv_stage, default=current.get("cisiv_stage") or "implementation")
    )
    next_output = dict(output) if output is not None else dict(current["output"])
    next_output["cisiv_stage"] = normalize_cisiv_stage(
        next_output.get("cisiv_stage"),
        default=next_cisiv_stage or "implementation",
    )
    next_cisiv_stage = next_output["cisiv_stage"]
    next_lease_owner = None if clear_lease else current.get("lease_owner") if lease_owner is _UNSET else lease_owner
    next_lease_expires_at = (
        None if clear_lease else current.get("lease_expires_at") if lease_expires_at is _UNSET else lease_expires_at
    )
    next_last_heartbeat_at = (
        None if clear_lease else current.get("last_heartbeat_at") if last_heartbeat_at is _UNSET else last_heartbeat_at
    )
    next_recovery_state = current.get("recovery_state") if recovery_state is _UNSET else recovery_state
    next_recovery_attempts = (
        int(current.get("recovery_attempts") or 0)
        if recovery_attempts is _UNSET
        else int(recovery_attempts or 0)
    )
    next_stale_reason = current.get("stale_reason") if stale_reason is _UNSET else stale_reason

    where_clauses = ["id = ?"]
    params: list = [workflow_run_id]
    if expected_statuses:
        placeholders = ", ".join("?" for _ in expected_statuses)
        where_clauses.append(f"status IN ({placeholders})")
        params.extend(expected_statuses)
    if expected_lease_owner is not None:
        where_clauses.append("lease_owner = ?")
        params.append(expected_lease_owner)

    with get_conn() as conn:
        cursor = conn.execute(
            f"""
            UPDATE workflow_runs
            SET status = ?,
                output_json = ?,
                cisiv_stage = ?,
                updated_at = ?,
                lease_owner = ?,
                lease_expires_at = ?,
                last_heartbeat_at = ?,
                recovery_state = ?,
                recovery_attempts = ?,
                stale_reason = ?
            WHERE {' AND '.join(where_clauses)}
            """,
            [
                next_status,
                json.dumps(next_output),
                next_cisiv_stage,
                now_iso(),
                next_lease_owner,
                next_lease_expires_at,
                next_last_heartbeat_at,
                next_recovery_state,
                next_recovery_attempts,
                next_stale_reason,
                *params,
            ],
        )
        if cursor.rowcount == 0:
            return None
    return get_workflow_run(workflow_run_id)


def claim_workflow_run_lease(
    workflow_run_id: str,
    from_statuses: list[str],
    to_status: str,
    lease_owner: str,
    lease_seconds: int,
) -> dict | None:
    if not from_statuses:
        return None
    placeholders = ", ".join("?" for _ in from_statuses)
    ts = now_iso()
    expires_at = offset_iso(lease_seconds)
    with get_conn() as conn:
        cursor = conn.execute(
            f"""
            UPDATE workflow_runs
            SET status = ?,
                updated_at = ?,
                lease_owner = ?,
                lease_expires_at = ?,
                last_heartbeat_at = ?,
                stale_reason = NULL
            WHERE id = ? AND status IN ({placeholders})
            """,
            [to_status, ts, lease_owner, expires_at, ts, workflow_run_id, *from_statuses],
        )
        if cursor.rowcount == 0:
            return None
    return get_workflow_run(workflow_run_id)


def renew_workflow_run_lease(workflow_run_id: str, lease_owner: str, lease_seconds: int) -> bool:
    ts = now_iso()
    expires_at = offset_iso(lease_seconds)
    with get_conn() as conn:
        cursor = conn.execute(
            """
            UPDATE workflow_runs
            SET updated_at = ?, lease_expires_at = ?, last_heartbeat_at = ?
            WHERE id = ? AND lease_owner = ? AND status = 'running'
            """,
            (ts, expires_at, ts, workflow_run_id, lease_owner),
        )
        return cursor.rowcount > 0


def _serialize_workflow_run_row(row) -> dict | None:
    if not row:
        return None
    output = _json_loads(row[3], {})
    cisiv_stage = normalize_cisiv_stage(row[4], default="implementation")
    output["cisiv_stage"] = normalize_cisiv_stage(output.get("cisiv_stage"), default=cisiv_stage)
    cisiv_stage = output["cisiv_stage"]
    return {
        "id": row[0],
        "workflow_id": row[1],
        "status": row[2],
        "output": output,
        "cisiv_stage": cisiv_stage,
        "created_at": row[5],
        "updated_at": row[6],
        "lease_owner": row[9],
        "lease_expires_at": row[10],
        "last_heartbeat_at": row[11],
        "recovery_state": row[12],
        "recovery_attempts": int(row[13] or 0),
        "stale_reason": row[14],
        "workflow": {
            "id": row[7],
            "name": row[8],
        } if row[7] else None,
    }


def get_workflow_run(workflow_run_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT wr.id, wr.workflow_id, wr.status, wr.output_json, wr.cisiv_stage, wr.created_at, wr.updated_at, w.id, w.name,
                   wr.lease_owner, wr.lease_expires_at, wr.last_heartbeat_at,
                   wr.recovery_state, wr.recovery_attempts, wr.stale_reason
            FROM workflow_runs wr
            LEFT JOIN workflows w ON w.id = wr.workflow_id
            WHERE wr.id = ?
            """,
            (workflow_run_id,),
        ).fetchone()
    return _serialize_workflow_run_row(row)


def list_workflow_runs(limit: int = 100) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT wr.id, wr.workflow_id, wr.status, wr.output_json, wr.cisiv_stage, wr.created_at, wr.updated_at, w.id, w.name,
                   wr.lease_owner, wr.lease_expires_at, wr.last_heartbeat_at,
                   wr.recovery_state, wr.recovery_attempts, wr.stale_reason
            FROM workflow_runs wr
            LEFT JOIN workflows w ON w.id = wr.workflow_id
            ORDER BY wr.created_at DESC, wr.updated_at DESC, wr.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_serialize_workflow_run_row(row) for row in rows]


def get_active_workflow_run(workflow_id: str) -> dict | None:
    placeholders = ", ".join("?" for _ in ACTIVE_WORKFLOW_RUN_STATUSES)
    with get_conn() as conn:
        row = conn.execute(
            f"""
            SELECT wr.id, wr.workflow_id, wr.status, wr.output_json, wr.cisiv_stage, wr.created_at, wr.updated_at, w.id, w.name,
                   wr.lease_owner, wr.lease_expires_at, wr.last_heartbeat_at,
                   wr.recovery_state, wr.recovery_attempts, wr.stale_reason
            FROM workflow_runs wr
            LEFT JOIN workflows w ON w.id = wr.workflow_id
            WHERE wr.workflow_id = ? AND wr.status IN ({placeholders})
            ORDER BY wr.created_at DESC, wr.updated_at DESC, wr.id DESC
            LIMIT 1
            """,
            (workflow_id, *ACTIVE_WORKFLOW_RUN_STATUSES),
        ).fetchone()
    return _serialize_workflow_run_row(row)


def list_expired_running_workflow_runs(expired_before: str, limit: int = 25) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT wr.id, wr.workflow_id, wr.status, wr.output_json, wr.cisiv_stage, wr.created_at, wr.updated_at, w.id, w.name,
                   wr.lease_owner, wr.lease_expires_at, wr.last_heartbeat_at,
                   wr.recovery_state, wr.recovery_attempts, wr.stale_reason
            FROM workflow_runs wr
            LEFT JOIN workflows w ON w.id = wr.workflow_id
            WHERE wr.status = 'running' AND COALESCE(wr.lease_expires_at, wr.updated_at) <= ?
            ORDER BY COALESCE(wr.lease_expires_at, wr.updated_at) ASC, wr.created_at ASC
            LIMIT ?
            """,
            (expired_before, limit),
        ).fetchall()
    return [_serialize_workflow_run_row(row) for row in rows]


def list_stale_workflow_runs(limit: int = 25) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT wr.id, wr.workflow_id, wr.status, wr.output_json, wr.cisiv_stage, wr.created_at, wr.updated_at, w.id, w.name,
                   wr.lease_owner, wr.lease_expires_at, wr.last_heartbeat_at,
                   wr.recovery_state, wr.recovery_attempts, wr.stale_reason
            FROM workflow_runs wr
            LEFT JOIN workflows w ON w.id = wr.workflow_id
            WHERE wr.status = 'stale'
            ORDER BY wr.updated_at ASC, wr.created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_serialize_workflow_run_row(row) for row in rows]


def mark_workflow_run_stale(workflow_run_id: str, reason: str, expired_before: str) -> dict | None:
    current = get_workflow_run(workflow_run_id)
    if not current or current["status"] != "running":
        return None

    output = dict(current.get("output") or {})
    output = _append_run_ledger(
        output,
        "stale",
        f"Workflow lease expired: {reason}",
        reason=reason,
        fromStatus=current["status"],
    )
    output.update(
        {
            "message": f"Workflow became stale: {reason}",
            "staleAt": now_iso(),
            "recoveryState": "stale",
            "staleReason": reason,
        }
    )

    with get_conn() as conn:
        cursor = conn.execute(
            """
            UPDATE workflow_runs
            SET status = 'stale',
                output_json = ?,
                updated_at = ?,
                lease_owner = NULL,
                lease_expires_at = NULL,
                last_heartbeat_at = NULL,
                recovery_state = 'stale',
                stale_reason = ?
            WHERE id = ? AND status = 'running' AND COALESCE(lease_expires_at, updated_at) <= ?
            """,
            (json.dumps(output), now_iso(), reason, workflow_run_id, expired_before),
        )
        if cursor.rowcount == 0:
            return None
    return get_workflow_run(workflow_run_id)


def begin_workflow_run_recovery(
    workflow_run_id: str,
    reason: str,
    max_recovery_attempts: int,
) -> dict | None:
    current = get_workflow_run(workflow_run_id)
    if not current or current["status"] != "stale":
        return None

    next_attempts = int(current.get("recovery_attempts") or 0) + 1
    output = dict(current.get("output") or {})

    if next_attempts > max_recovery_attempts:
        output = _append_run_ledger(
            output,
            "recovery_failed",
            "Workflow exceeded the recovery limit and was marked failed.",
            attempt=next_attempts,
            reason=reason,
        )
        output.update(
            {
                "message": "Workflow exceeded recovery attempts and was marked failed.",
                "error": "Workflow recovery limit reached.",
                "failedAt": now_iso(),
                "recoveryState": "exhausted",
                "recoveryAttempts": next_attempts,
            }
        )
        return update_workflow_run(
            workflow_run_id,
            status="failed",
            output=output,
            expected_statuses=["stale"],
            recovery_state="exhausted",
            recovery_attempts=next_attempts,
            stale_reason=reason,
            clear_lease=True,
        )

    output = _append_run_ledger(
        output,
        "recovery_queued",
        "Workflow recovery was queued.",
        attempt=next_attempts,
        reason=reason,
    )
    output.update(
        {
            "message": f"Workflow recovery queued (attempt {next_attempts}).",
            "recoveryState": "queued",
            "recoveringAt": now_iso(),
            "recoveryAttempts": next_attempts,
        }
    )
    return update_workflow_run(
        workflow_run_id,
        status="recovering",
        output=output,
        expected_statuses=["stale"],
        recovery_state="queued",
        recovery_attempts=next_attempts,
        stale_reason=reason,
        clear_lease=True,
    )


def mark_workflow_run_recovery_enqueue_failed(workflow_run_id: str, error: str) -> dict | None:
    current = get_workflow_run(workflow_run_id)
    if not current or current["status"] != "recovering":
        return None

    output = dict(current.get("output") or {})
    output = _append_run_ledger(
        output,
        "recovery_enqueue_failed",
        "Workflow recovery could not be enqueued.",
        error=error,
        attempt=int(current.get("recovery_attempts") or 0),
    )
    output.update(
        {
            "message": "Workflow recovery could not be queued yet.",
            "recoveryState": "enqueue_failed",
            "recoveryEnqueueError": error,
            "lastRecoveryFailureAt": now_iso(),
        }
    )
    return update_workflow_run(
        workflow_run_id,
        status="stale",
        output=output,
        expected_statuses=["recovering"],
        recovery_state="enqueue_failed",
        stale_reason=current.get("stale_reason") or "recovery enqueue failed",
        clear_lease=True,
    )

def create_workflow_approval(
    workflow_run_id: str,
    workflow_id: str,
    step_id: str,
    step_label: str,
    step_type: str,
    reason: str | None,
    payload: dict,
    cisiv_stage: str | None = None,
) -> dict | None:
    approval_id = str(uuid.uuid4())
    ts = now_iso()
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="implementation")
    normalized_payload = dict(payload or {})
    normalized_payload["cisiv_stage"] = normalize_cisiv_stage(
        normalized_payload.get("cisiv_stage"),
        default=normalized_cisiv_stage,
    )
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO workflow_approvals (
                id, workflow_run_id, workflow_id, step_id, step_label, step_type, status, reason, payload_json, cisiv_stage, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                approval_id,
                workflow_run_id,
                workflow_id,
                step_id,
                step_label,
                step_type,
                "pending",
                reason,
                json.dumps(normalized_payload),
                normalized_payload["cisiv_stage"],
                ts,
                ts,
            ),
        )
    return get_workflow_approval(approval_id)

def _serialize_workflow_approval_row(row) -> dict | None:
    if not row:
        return None
    payload = _json_loads(row[8], {})
    cisiv_stage = normalize_cisiv_stage(row[9], default="implementation")
    payload["cisiv_stage"] = normalize_cisiv_stage(payload.get("cisiv_stage"), default=cisiv_stage)
    cisiv_stage = payload["cisiv_stage"]
    workflow = None
    if row[11]:
        workflow = {"id": row[11], "name": row[12]}
    return {
        "id": row[0],
        "workflow_run_id": row[1],
        "workflow_id": row[2],
        "step_id": row[3],
        "step_label": row[4],
        "step_type": row[5],
        "status": row[6],
        "reason": row[7],
        "payload": payload,
        "cisiv_stage": cisiv_stage,
        "created_at": row[10],
        "updated_at": row[13],
        "workflow_run": {
            "id": row[1],
            "workflow": workflow,
        },
    }

def get_workflow_approval(approval_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT wa.id, wa.workflow_run_id, wa.workflow_id, wa.step_id, wa.step_label, wa.step_type,
                   wa.status, wa.reason, wa.payload_json, wa.cisiv_stage, wa.created_at, w.id, w.name, wa.updated_at
            FROM workflow_approvals wa
            LEFT JOIN workflows w ON w.id = wa.workflow_id
            WHERE wa.id = ?
            """,
            (approval_id,),
        ).fetchone()
    return _serialize_workflow_approval_row(row)

def get_latest_workflow_approval_for_step(workflow_run_id: str, step_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT wa.id, wa.workflow_run_id, wa.workflow_id, wa.step_id, wa.step_label, wa.step_type,
                   wa.status, wa.reason, wa.payload_json, wa.cisiv_stage, wa.created_at, w.id, w.name, wa.updated_at
            FROM workflow_approvals wa
            LEFT JOIN workflows w ON w.id = wa.workflow_id
            WHERE wa.workflow_run_id = ? AND wa.step_id = ?
            ORDER BY wa.created_at DESC
            LIMIT 1
            """,
            (workflow_run_id, step_id),
        ).fetchone()
    return _serialize_workflow_approval_row(row)

def list_pending_workflow_approvals(limit: int = 100) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT wa.id, wa.workflow_run_id, wa.workflow_id, wa.step_id, wa.step_label, wa.step_type,
                   wa.status, wa.reason, wa.payload_json, wa.cisiv_stage, wa.created_at, w.id, w.name, wa.updated_at
            FROM workflow_approvals wa
            LEFT JOIN workflows w ON w.id = wa.workflow_id
            WHERE wa.status = 'pending'
            ORDER BY wa.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_serialize_workflow_approval_row(row) for row in rows]

def update_workflow_approval(approval_id: str, status: str) -> dict | None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE workflow_approvals SET status = ?, updated_at = ? WHERE id = ?",
            (status, now_iso(), approval_id),
        )
    return get_workflow_approval(approval_id)

def get_onboarding_state() -> dict:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT onboarding_done, goal, tools_json, created_at, updated_at, cisiv_stage
            FROM app_profile
            WHERE id = 1
            """
        ).fetchone()
    if not row:
        return {
            "onboarding_done": False,
            "goal": "",
            "tools": [],
            "created_at": None,
            "updated_at": None,
            "cisiv_stage": "identity",
        }
    return {
        "onboarding_done": bool(row[0]),
        "goal": row[1] or "",
        "tools": _json_loads(row[2], []),
        "created_at": row[3],
        "updated_at": row[4],
        "cisiv_stage": normalize_cisiv_stage(row[5], default="identity"),
    }

def complete_onboarding(goal: str, tools: list[str], cisiv_stage: str | None = None) -> dict:
    current = get_onboarding_state()
    ts = now_iso()
    normalized_cisiv_stage = normalize_cisiv_stage(cisiv_stage, default="identity")
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO app_profile (id, onboarding_done, goal, tools_json, cisiv_stage, created_at, updated_at)
            VALUES (1, 1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                onboarding_done = 1,
                goal = excluded.goal,
                tools_json = excluded.tools_json,
                cisiv_stage = excluded.cisiv_stage,
                updated_at = excluded.updated_at
            """,
            (
                goal,
                json.dumps(tools),
                normalized_cisiv_stage,
                current["created_at"] or ts,
                ts,
            ),
        )
    return get_onboarding_state()
