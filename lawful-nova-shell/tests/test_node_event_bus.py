from __future__ import annotations

import json


def test_event_bus_matches_wildcards_persists_and_bounds_history(tmp_path, monkeypatch) -> None:
    from nova.node.event_bus import EventBus

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    seen = []
    bus = EventBus(channels=["tool.*", "governance.*"], max_events=2)
    bus.subscribe("tool.*", seen.append)

    bus.emit("tool.invoked", "started", {"tool_name": "code"})
    bus.emit("governance.receipt_verified", "verified", {"trace_id": "trace-1"})
    bus.emit("tool.completed", "completed", {"tool_name": "code"})

    assert [event.channel for event in seen] == ["tool.invoked", "tool.completed"]
    assert [event.channel for event in bus.history()] == ["governance.receipt_verified", "tool.completed"]
    assert [event.channel for event in bus.history("tool.")] == ["tool.completed"]

    lines = (tmp_path / "event-bus.jsonl").read_text(encoding="utf-8").splitlines()
    persisted = [json.loads(line) for line in lines]
    assert [event["channel"] for event in persisted] == [
        "tool.invoked",
        "governance.receipt_verified",
        "tool.completed",
    ]


def test_event_bus_emits_canonical_substrate_events(tmp_path, monkeypatch) -> None:
    from nova.node.event_bus import EventBus
    from nova.node.substrate_events import read_substrate_events

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    bus = EventBus(channels=["tool.*", "governance.*"], max_events=10)

    invoked = bus.emit(
        "tool.invoked",
        "started",
        {
            "tool_name": "code",
            "trace_id": "trace-1",
            "args_hash": "sha256:args",
            "governed_state": "allowed",
        },
    )
    completed = bus.emit(
        "tool.completed",
        "completed",
        {
            "tool_name": "code",
            "trace_id": "trace-1",
            "output_hash": "sha256:out",
            "duration_ms": 12,
        },
    )

    events = read_substrate_events(limit=10)

    assert [event["type"] for event in events] == ["Capability.Invoked", "Capability.Completed"]
    assert [event["sequence"] for event in events] == [1, 2]
    assert events[0]["eventId"].startswith("evt_")
    assert events[0]["kernel"] == "UL"
    assert events[0]["streamId"] == "capability:code"
    assert events[0]["intent"] == {"intentId": "trace-1", "source": "AGENT"}
    assert events[0]["payload"]["type"] == "Capability.Invoked"
    assert events[0]["payload"]["name"] == "code"
    assert events[0]["payload"]["capabilityKind"] == "MODEL_CALL"
    assert events[0]["payload"]["riskLevel"] == "MEDIUM"
    assert events[0]["metadata"]["schemaVersion"] == "substrate-event-v1"
    assert events[0]["metadata"]["governanceDecision"]["result"] == "ALLOWED"
    assert events[0]["metadata"]["extensions"]["legacyEventId"] == invoked.id
    assert events[1]["parentEventIds"] == [events[0]["eventId"]]
    assert events[1]["payload"]["receiptId"] == "trace-1"
    assert events[1]["metadata"]["extensions"]["legacyEventId"] == completed.id

    lines = (tmp_path / "substrate-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["type"] == "Capability.Invoked"


def test_node_event_and_feature_manifest_routes(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api
    from nova.node.event_bus import get_event_bus

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    get_event_bus().emit("node.online", "health_check", {"status": "ok"})

    client = TestClient(nova_api.app)
    events = client.get("/node/events").json()
    manifest = client.get("/node/feature-manifest").json()

    assert events["events"][-1]["channel"] == "node.online"
    assert "governance.*" in events["channels"]
    assert manifest["manifest"]["modules"]["core"] == [
        "file_search",
        "symbol_search",
        "patch_manager",
        "terminal",
        "test_runner",
        "git_panel",
    ]
    assert "on_tool_invoked" in manifest["manifest"]["runtime"]["hooks"]
    assert "on_patch_generated" in manifest["manifest"]["runtime"]["hooks"]
    assert "tool.*" in manifest["manifest"]["event_bus"]["channels"]
    assert manifest["manifest"]["event_bus"]["canonical_stream"]["format"] == "jsonl"
    assert "substrate.*" in manifest["manifest"]["event_bus"]["channels"]
    assert "explain_tool" in manifest["manifest"]["modules"]["nova_specific"]


def test_node_substrate_event_route_filters_by_stream(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api
    from nova.node.substrate_events import append_substrate_event, make_substrate_event

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    append_substrate_event(
        make_substrate_event(
            type_="Nova.StatusChanged",
            kernel="Governance",
            stream_id="status",
            payload={"type": "Nova.StatusChanged", "status": "IDLE"},
        )
    )
    append_substrate_event(
        make_substrate_event(
            type_="Reasoning.Chunk",
            kernel="UL",
            stream_id="reasoning",
            payload={"type": "Reasoning.Chunk", "content": "Checking invariants"},
        )
    )

    client = TestClient(nova_api.app)
    payload = client.get("/node/substrate-events?stream_id=reasoning").json()

    assert payload["schemaVersion"] == "substrate-event-v1"
    assert payload["canonical"] == "jsonl"
    assert payload["events"][0]["type"] == "Reasoning.Chunk"
    assert payload["events"][0]["streamId"] == "reasoning"


def test_status_lists_event_bus_surface(tmp_path, monkeypatch) -> None:
    from nova.node.status import node_status

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    status = node_status()

    assert "/node/events" in status["endpoints"]
    assert "/node/feature-manifest" in status["endpoints"]
    assert "/node/substrate-events" in status["endpoints"]
    assert status["governance_health"]["event_bus_events"] == 0
