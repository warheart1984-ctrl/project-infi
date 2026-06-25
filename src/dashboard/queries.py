"""Read-only SQLite queries for CORI Alpha observability."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.cori.payload_fields import (
    envelope_asset_id,
    envelope_execution_id,
    envelope_law_eval_id,
    envelope_mission_id,
    envelope_steward,
    parse_payload,
)
from src.cori.store_paths import continuity_store_path, law_ledger_path, panel_store_path


def open_sqlite(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"DB not found: {path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def fetch_one(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def list_mission_summaries(*, limit: int = 100) -> list[dict[str, Any]]:
    """Aggregate governed mission stream from continuity events."""
    conn = open_sqlite(continuity_store_path())
    try:
        rows = fetch_all(
            conn,
            """
            SELECT created_at, event_type, payload_json
            FROM continuity_events
            WHERE event_type IN ('urg_mission', 'law_eval', 'aaes_exec', 'nexus_event')
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
    finally:
        conn.close()

    missions: dict[str, dict[str, Any]] = {}
    for row in rows:
        payload = parse_payload(row["payload_json"])
        mission_id = envelope_mission_id(payload)
        key = mission_id or f"anon-{row['created_at']}"
        summary = missions.setdefault(
            key,
            {
                "time": row["created_at"],
                "steward": envelope_steward(payload),
                "mission_id": mission_id or None,
                "law_eval_id": None,
                "aaes_exec_id": None,
                "nexus_event_id": None,
                "status": None,
            },
        )
        law_id = envelope_law_eval_id(payload)
        if law_id:
            summary["law_eval_id"] = summary["law_eval_id"] or law_id
        exec_id = envelope_execution_id(payload)
        if exec_id and row["event_type"] in {"aaes_exec", "nexus_event"}:
            if row["event_type"] == "aaes_exec":
                summary["aaes_exec_id"] = summary["aaes_exec_id"] or exec_id
            else:
                summary["nexus_event_id"] = summary["nexus_event_id"] or exec_id
        status = payload.get("status") or (payload.get("payload") or {}).get("status")
        if status:
            summary["status"] = summary["status"] or str(status)
    return list(missions.values())


def trace_mission_events(mission_id: str) -> list[dict[str, Any]]:
    conn = open_sqlite(continuity_store_path())
    try:
        rows = fetch_all(
            conn,
            """
            SELECT event_type, payload_json, created_at
            FROM continuity_events
            WHERE payload_json LIKE '%' || ? || '%'
            ORDER BY created_at ASC
            """,
            (mission_id,),
        )
    finally:
        conn.close()
    return [
        {
            "event_type": row["event_type"],
            "payload": parse_payload(row["payload_json"]),
            "time": row["created_at"],
        }
        for row in rows
    ]


def law_kernel_rows(*, limit: int = 50) -> dict[str, Any]:
    conn = open_sqlite(law_ledger_path())
    try:
        laws = fetch_all(
            conn,
            """
            SELECT law_id, introduced_by, created_at_epoch, law_hash, status, current_fitness
            FROM law_records
            ORDER BY created_at_epoch DESC
            LIMIT ?
            """,
            (limit,),
        )
        fitness = fetch_all(
            conn,
            """
            SELECT law_id, epoch, fitness, sample_size, notes
            FROM law_fitness_history
            ORDER BY epoch DESC
            LIMIT ?
            """,
            (limit,),
        )
    finally:
        conn.close()
    return {
        "laws": [dict(row) for row in laws],
        "fitness_history": [dict(row) for row in fitness],
    }


def evidence_density_for_asset(asset_id: str) -> dict[str, Any]:
    conn = open_sqlite(continuity_store_path())
    try:
        rows = fetch_all(
            conn,
            """
            SELECT event_type, payload_json, created_at
            FROM continuity_events
            WHERE payload_json LIKE '%' || ? || '%'
            ORDER BY created_at DESC
            """,
            (asset_id,),
        )
    finally:
        conn.close()

    events: list[dict[str, Any]] = []
    for row in rows:
        payload = parse_payload(row["payload_json"])
        if envelope_asset_id(payload) != asset_id and asset_id not in row["payload_json"]:
            continue
        events.append(
            {
                "type": row["event_type"],
                "payload": payload,
                "time": row["created_at"],
            }
        )
    return {
        "asset_id": asset_id,
        "events": events,
        "evidence_count": sum(1 for e in events if str(e["type"]).startswith("evidence")),
    }


def panels_referencing(needle: str) -> list[dict[str, Any]]:
    conn = open_sqlite(panel_store_path())
    try:
        rows = fetch_all(
            conn,
            "SELECT id, panel_type, payload_json, steward_identity, created_at FROM panels WHERE payload_json LIKE '%' || ? || '%'",
            (needle,),
        )
    finally:
        conn.close()
    return [
        {
            "id": row["id"],
            "panel_type": row["panel_type"],
            "payload": parse_payload(row["payload_json"]),
            "steward_identity": row["steward_identity"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
