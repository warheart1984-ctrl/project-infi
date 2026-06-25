from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import db as app_db
from app import main as app_main


def _client(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", tmp_path / "continuity.db")
    monkeypatch.setattr(app_main, "CONTINUITY_WORKSPACE_ROOT", tmp_path)
    app_db.init_db()
    return TestClient(app_main.app)


def _columns(table_name: str) -> list[str]:
    with app_db.get_conn() as conn:
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]


def test_substrate_tables_use_v0_schema_only(tmp_path, monkeypatch):
    _client(tmp_path, monkeypatch)

    assert _columns("events") == ["id", "timestamp", "name", "parent_id", "payload"]
    assert _columns("receipts") == ["id", "event_id", "status", "details", "timestamp"]
    assert _columns("file_events") == ["id", "event_id", "path", "timestamp"]


def test_event_timeline_and_alias_routes(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    created = client.post("/events", json={"name": "TestEvent", "payload": {"kind": "manual"}})
    assert created.status_code == 200
    event = created.json()["event"]
    assert event["name"] == "TestEvent"
    assert event["parentId"] is None
    assert event["payload"] == {"kind": "manual"}
    assert isinstance(event["timestamp"], int)

    listed = client.get("/api/continuity/events")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["events"]] == [event["id"]]


def test_lineage_returns_anchor_then_parents(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    root = client.post("/api/continuity/events", json={"name": "Root"}).json()["event"]
    child = client.post("/events", json={"name": "Child", "parentId": root["id"]}).json()["event"]

    response = client.get(f"/lineage/{child['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["event"]["id"] == child["id"]
    lineage = body["lineage"]
    assert [(item["event"]["name"], item["depth"]) for item in lineage] == [("Child", 0), ("Root", 1)]


def test_receipts_link_to_events_and_reject_missing_events(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    event = client.post("/events", json={"name": "ReceiptAnchor"}).json()["event"]
    created = client.post("/receipts", json={"eventId": event["id"], "status": "PASS", "details": "validated"})
    assert created.status_code == 200
    receipt = created.json()["receipt"]
    assert receipt["eventId"] == event["id"]
    assert receipt["status"] == "PASS"
    assert receipt["details"] == "validated"

    listed = client.get("/api/continuity/receipts")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["receipts"]] == [receipt["id"]]

    missing = client.post("/receipts", json={"eventId": "missing-event", "status": "PASS"})
    assert missing.status_code == 404


def test_file_open_and_save_emit_linked_file_events(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    sample = tmp_path / "notes.txt"
    sample.write_text("first draft", encoding="utf-8")

    opened = client.post("/file/open", json={"path": "notes.txt"})
    assert opened.status_code == 200
    opened_body = opened.json()
    assert opened_body["content"] == "first draft"
    open_event = opened_body["event"]
    assert open_event["name"] == "File.Opened"
    assert open_event["payload"]["path"] == "notes.txt"

    saved = client.post("/api/continuity/file/save", json={"path": "notes.txt", "content": "second draft"})
    assert saved.status_code == 200
    save_event = saved.json()["event"]
    assert sample.read_text(encoding="utf-8") == "second draft"
    assert save_event["name"] == "File.Saved"
    assert save_event["parentId"] == open_event["id"]

    lineage = client.get(f"/lineage/{save_event['id']}").json()["lineage"]
    assert [item["event"]["name"] for item in lineage] == ["File.Saved", "File.Opened"]


def test_file_paths_must_stay_inside_workspace(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.post("/file/save", json={"path": "../escape.txt", "content": "nope"})

    assert response.status_code == 400
