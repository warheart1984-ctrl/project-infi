"""HTTP API tests for agent profiles, task detail, and follow-up."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import operator_kernel.main as main_mod
from operator_kernel.events import TaskEventStore
from operator_kernel.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    store = TaskEventStore(tmp_path / "tasks")
    monkeypatch.setattr(main_mod, "STORE", store)
    return TestClient(app)


def test_list_profiles(client: TestClient) -> None:
    r = client.get("/agent/profiles")
    assert r.status_code == 200
    profiles = r.json()
    ids = {p["id"] for p in profiles}
    assert {"explorer", "builder", "reviewer"} <= ids


def test_create_and_get_task(client: TestClient) -> None:
    with patch.object(main_mod, "start_task", return_value="tid-1"):
        created = client.post(
            "/agent/tasks",
            json={
                "goal": "List Python files",
                "agent_id": "explorer",
                "constraints": {"read_only": True, "allow_shell": False, "max_steps": 3},
            },
        )
    assert created.status_code == 200
    assert created.json()["task_id"] == "tid-1"

    main_mod.STORE.write_meta(
        "tid-1",
        {
            "task_id": "tid-1",
            "goal": "List Python files",
            "title": "List Python files",
            "agent_id": "explorer",
            "status": "completed",
            "messages": [{"role": "user", "content": "List Python files"}],
        },
    )
    main_mod.STORE.append("tid-1", "task_created", {"goal": "List Python files"})

    detail = client.get("/agent/tasks/tid-1")
    assert detail.status_code == 200
    body = detail.json()
    assert body["task_id"] == "tid-1"
    assert body["meta"]["agent_id"] == "explorer"
    assert len(body["events"]) >= 1


def test_append_message_starts_continue(client: TestClient) -> None:
    main_mod.STORE.write_meta(
        "tid-2",
        {
            "task_id": "tid-2",
            "goal": "first",
            "status": "completed",
            "messages": [{"role": "user", "content": "first"}],
        },
    )

    with patch.object(main_mod, "continue_task") as cont:
        r = client.post("/agent/tasks/tid-2/message", json={"text": "now do tests"})
    assert r.status_code == 200
    assert r.json()["status"] == "running"
    cont.assert_called_once()


def test_append_message_404(client: TestClient) -> None:
    r = client.post("/agent/tasks/missing/message", json={"text": "hi"})
    assert r.status_code == 404


def test_cancel_task_not_found(client: TestClient) -> None:
    r = client.post("/agent/tasks/missing/cancel")
    assert r.status_code == 404


def test_cancel_task_not_running(client: TestClient) -> None:
    main_mod.STORE.write_meta(
        "tid-done",
        {"task_id": "tid-done", "goal": "x", "status": "completed"},
    )
    r = client.post("/agent/tasks/tid-done/cancel")
    assert r.status_code == 409


def test_cancel_task_idempotent(client: TestClient) -> None:
    main_mod.STORE.write_meta(
        "tid-cancelled",
        {"task_id": "tid-cancelled", "goal": "x", "status": "cancelled"},
    )
    r = client.post("/agent/tasks/tid-cancelled/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_cancel_task_running(client: TestClient) -> None:
    main_mod.STORE.write_meta(
        "tid-run",
        {"task_id": "tid-run", "goal": "x", "status": "running"},
    )
    with (
        patch.object(main_mod, "is_task_running", return_value=True),
        patch.object(main_mod, "request_cancel", return_value=True),
    ):
        r = client.post("/agent/tasks/tid-run/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelling"
    meta = main_mod.STORE.read_meta("tid-run")
    assert meta["status"] == "cancelling"
