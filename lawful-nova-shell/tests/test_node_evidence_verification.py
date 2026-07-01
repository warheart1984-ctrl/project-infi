from __future__ import annotations


def test_verify_tool_trace_reconstructs_receipt_events_manifest_and_hashes(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api
    from nova.node.tools import coder_tool
    from nova.node.tools import replay_coding

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(coder_tool, "generate", lambda prompt, **kwargs: "def health():\n    return 'ok'\n")
    monkeypatch.setattr(replay_coding, "generate", lambda prompt, **kwargs: "def health():\n    return 'ok'\n")

    client = TestClient(nova_api.app)
    created = client.post(
        "/node/tool",
        json={
            "task_id": "task-evidence-001",
            "intent": "code",
            "caller_id": "cursor",
            "file_path": "src/app.py",
            "instruction": "Add health endpoint",
            "current_code": "def old():\n    return 'old'\n",
        },
    ).json()

    trace_id = created["governance"]["trace_id"]
    evidence = client.get(f"/node/verify/{trace_id}").json()

    assert evidence["trace_id"] == trace_id
    assert evidence["receipt"]["trace_id"] == trace_id
    assert evidence["verification"]["receipt_hash"]["valid"] is True
    assert evidence["verification"]["input_hash"]["valid"] is True
    assert evidence["verification"]["output_hash"]["valid"] is True
    assert evidence["verification"]["original_code_hash"]["valid"] is True
    assert evidence["verification"]["replay"]["available"] is True
    assert evidence["verification"]["replay"]["deterministic"] is True
    assert evidence["policy"]["version"] == "1.0"
    assert evidence["policy"]["manifest"]["node"]["description"] == "Sovereign Node feature manifest for Nova Desktop"
    assert [event["channel"] for event in evidence["trace"]["events"]] == [
        "tool.invoked",
        "governance.patch_generated",
        "tool.completed",
        "governance.receipt_verified",
    ]
    assert any(event["kind"] == "nodeToolReceipt" for event in evidence["trace"]["continuity"])
    assert evidence["cross_node"]["comparable"] is True
    assert "receipt_hash" in evidence["cross_node"]["compare_keys"]


def test_compare_receipts_reports_matching_and_drift(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api
    from nova.node.tools.receipts import write_coding_receipt

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    write_coding_receipt(
        trace_id="trace-compare-1",
        task={
            "intent": "code",
            "file_path": "src/app.py",
            "instruction": "Add comment",
            "current_code": "print('x')\n",
        },
        governance={"decision": "allowed", "policy_version": "1.0", "receipts": ["continuity"]},
        result={"updated_code": "# ok\nprint('x')\n", "diff": "+# ok", "receipts": ["coder_tool"]},
        tool="code",
    )

    client = TestClient(nova_api.app)
    receipt = client.get("/node/verify/trace-compare-1").json()["receipt"]
    same = client.post("/node/compare-receipts", json={"left": receipt, "right": receipt}).json()
    drift = client.post(
        "/node/compare-receipts",
        json={"left": receipt, "right": {**receipt, "output_hash": "sha256:drift"}},
    ).json()

    assert same["matching"] is True
    assert same["matches"]["receipt_hash"] is True
    assert drift["matching"] is False
    assert drift["matches"]["output_hash"] is False
    assert "output_hash" in drift["drift_keys"]
