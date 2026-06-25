"""
Live SQLite invariant tests — run against populated data/ stores after governed missions.

Enable with:
  CORI_LIVE_INVARIANTS=1 pytest tests/test_runtime_governance_invariants_live.py -q

Or run after `cori mission "..."` when data/*.sqlite3 exist (auto-skips if missing).
"""

from __future__ import annotations

import json
import os
import sqlite3

import pytest

from src.cori.payload_fields import (
    envelope_asset_id,
    envelope_execution_id,
    envelope_law_eval_id,
    envelope_validation_ref,
    parse_payload,
)
from src.cori.store_paths import continuity_store_path, law_ledger_path, panel_store_path
from src.dashboard import queries

pytestmark = pytest.mark.live_db


def _live_enabled() -> bool:
    return os.environ.get("CORI_LIVE_INVARIANTS", "").strip().lower() in {"1", "true", "yes"}


def _require_live_dbs() -> dict[str, sqlite3.Connection]:
    paths = {
        "panel": panel_store_path(),
        "law": law_ledger_path(),
        "cont": continuity_store_path(),
    }
    if not _live_enabled():
        for path in paths.values():
            if not path.is_file():
                pytest.skip(
                    "Live invariant DBs not found; run a governed mission first or set CORI_LIVE_INVARIANTS=1"
                )
    missing = [f"{name}={path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        pytest.skip(f"Missing live DBs: {', '.join(missing)}")

    conns: dict[str, sqlite3.Connection] = {}
    for name, path in paths.items():
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conns[name] = conn
    return conns


@pytest.fixture(scope="module")
def dbs():
    conns = _require_live_dbs()
    yield conns
    for conn in conns.values():
        conn.close()


def _fetch_all(conn: sqlite3.Connection, sql: str, params: tuple = ()):
    return list(conn.execute(sql, params).fetchall())


def _fetch_one(conn: sqlite3.Connection, sql: str, params: tuple = ()):
    return conn.execute(sql, params).fetchone()


def test_no_execution_without_validation(dbs):
    """Invariant 1: aaes_exec requires validation_decided and law_eval."""
    cont = dbs["cont"]
    rows = _fetch_all(
        cont,
        "SELECT id, payload_json FROM continuity_events WHERE event_type = 'aaes_exec'",
    )
    if not rows:
        pytest.skip("No aaes_exec events; run a governed mission first.")

    for row in rows:
        payload = parse_payload(row["payload_json"])
        law_eval_id = envelope_law_eval_id(payload)
        validation_ref = envelope_validation_ref(payload)
        assert law_eval_id, f"aaes_exec {row['id']} missing law_eval_id"
        assert validation_ref, f"aaes_exec {row['id']} missing validation reference"

        v = _fetch_one(
            cont,
            """
            SELECT id FROM continuity_events
            WHERE event_type = 'validation_decided'
              AND payload_json LIKE '%' || ? || '%'
            LIMIT 1
            """,
            (validation_ref,),
        )
        assert v, f"validation_decided {validation_ref} not found for aaes_exec {row['id']}"

        l = _fetch_one(
            cont,
            """
            SELECT id FROM continuity_events
            WHERE event_type = 'law_eval'
              AND payload_json LIKE '%' || ? || '%'
            LIMIT 1
            """,
            (law_eval_id,),
        )
        assert l, f"law_eval {law_eval_id} not found for aaes_exec {row['id']}"


def test_no_validation_without_evidence(dbs):
    """Invariant 2: validation_decided must have evidence_attached for the asset."""
    cont = dbs["cont"]
    validations = _fetch_all(
        cont,
        "SELECT id, payload_json FROM continuity_events WHERE event_type = 'validation_decided'",
    )
    if not validations:
        pytest.skip("No validation_decided events.")

    for row in validations:
        payload = parse_payload(row["payload_json"])
        asset_id = envelope_asset_id(payload)
        assert asset_id, f"validation_decided {row['id']} missing asset_id"

        evidence = _fetch_one(
            cont,
            """
            SELECT id FROM continuity_events
            WHERE event_type LIKE 'evidence_%'
              AND payload_json LIKE '%' || ? || '%'
            LIMIT 1
            """,
            (asset_id,),
        )
        assert evidence, f"No evidence for asset {asset_id} (validation {row['id']})"


def test_no_governed_mission_without_law_eval(dbs):
    """Invariant 3: governed urg_mission must reference a continuity law_eval."""
    cont = dbs["cont"]
    missions = _fetch_all(
        cont,
        "SELECT id, payload_json FROM continuity_events WHERE event_type = 'urg_mission'",
    )
    if not missions:
        pytest.skip("No URG missions recorded.")

    for row in missions:
        payload = parse_payload(row["payload_json"])
        if not payload.get("governed", False) and not (payload.get("payload") or {}).get("governed"):
            continue
        law_eval_id = envelope_law_eval_id(payload)
        assert law_eval_id, f"URG mission {row['id']} governed but missing law_eval_id"
        found = _fetch_one(
            cont,
            """
            SELECT id FROM continuity_events
            WHERE event_type = 'law_eval'
              AND payload_json LIKE '%' || ? || '%'
            LIMIT 1
            """,
            (law_eval_id,),
        )
        assert found, f"law_eval {law_eval_id} not found for URG mission {row['id']}"


def test_nova_introduced_laws_have_ledger_entry(dbs):
    """Invariant 4: introduced_by=nova laws must have a law_ledger entry with hash."""
    law = dbs["law"]
    rows = _fetch_all(law, "SELECT law_id, law_hash FROM law_records WHERE introduced_by = 'nova'")
    if not rows:
        pytest.skip("No nova-introduced laws in law_records.")

    for row in rows:
        law_id = row["law_id"]
        assert row["law_hash"], f"law {law_id} missing law_hash"
        ledger = _fetch_one(
            law,
            "SELECT entry_id, law_hash FROM law_ledger WHERE law_id = ? LIMIT 1",
            (law_id,),
        )
        assert ledger, f"law {law_id} missing law_ledger entry"
        assert ledger["law_hash"], f"law_ledger entry for {law_id} missing hash"


def test_panels_reference_executions(dbs):
    """Invariant 5: aaes_exec / nexus_event ids appear in panel_store payloads."""
    cont = dbs["cont"]
    execs = _fetch_all(
        cont,
        "SELECT id, payload_json FROM continuity_events WHERE event_type IN ('aaes_exec', 'nexus_event')",
    )
    if not execs:
        pytest.skip("No execution or nexus events.")

    for row in execs:
        payload = parse_payload(row["payload_json"])
        exec_id = envelope_execution_id(payload)
        assert exec_id, f"continuity event {row['id']} missing execution id"
        panels = queries.panels_referencing(exec_id)
        assert panels, f"No panel references {exec_id} (continuity {row['id']})"


def test_dashboard_missions_readable():
    """Smoke: dashboard query layer can read mission stream from live DBs."""
    if not continuity_store_path().is_file():
        pytest.skip("continuity store missing")
    rows = queries.list_mission_summaries(limit=10)
    assert isinstance(rows, list)
