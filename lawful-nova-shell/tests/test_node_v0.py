from __future__ import annotations

import json


def test_node_v0_status_submit_result_and_continuity_log(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    class FakeProvider:
        provider_id = "local"
        model = "nova-local"

        def chat_completion(self, governed_request):
            text = governed_request["messages"][-1]["content"]
            return {
                "completion": {
                    "id": "node-completion-1",
                    "object": "chat.completion",
                    "created": 123,
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {"role": "assistant", "content": f"node:{text}"},
                        }
                    ],
                },
                "receipt": {"provider": "local", "deterministic_core": True},
            }

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("NOVA_NODE_ID", "node-test-001")
    monkeypatch.setenv("NOVA_OPERATOR_KEY_ID", "operator-test-key")
    monkeypatch.delenv("NOVA_PROVIDER", raising=False)
    monkeypatch.setattr(nova_api, "build_provider", lambda config: FakeProvider())

    client = TestClient(nova_api.app)
    status = client.get("/node/status").json()

    assert status["node_id"] == "node-test-001"
    assert status["operator_key_id"] == "operator-test-key"
    assert status["policy_version"] == "1.0"
    assert status["conformance_profile"] == "N0"
    assert status["receipt_count"] == 0
    assert "/node/submit" in status["endpoints"]
    assert "/node/result/{trace_id}" in status["endpoints"]

    submit = client.post(
        "/node/submit",
        json={
            "task_id": "task-001",
            "intent": "chat",
            "caller_id": "cursor",
            "payload": {"messages": [{"role": "user", "content": "hello node"}]},
        },
    ).json()

    assert submit["decision"] == "allowed"
    assert submit["trace_id"]
    assert submit["result"]["output"] == "node:hello node"
    assert submit["receipt"]["task_id"] == "task-001"
    assert submit["receipt"]["node_id"] == "node-test-001"
    assert submit["receipt"]["operator_key_id"] == "operator-test-key"
    assert submit["receipt"]["model_id"] == "nova-local"
    assert submit["receipt"]["policy_version"] == "1.0"
    assert submit["receipt"]["input_hash"].startswith("sha256:")
    assert submit["receipt"]["output_hash"].startswith("sha256:")
    assert submit["receipt"]["receipt_hash"].startswith("sha256:")
    assert submit["receipts"] == [submit["receipt"]["receipt_hash"]]

    result = client.get(f"/node/result/{submit['trace_id']}").json()
    assert result["trace_id"] == submit["trace_id"]
    assert result["receipt"]["receipt_hash"] == submit["receipt"]["receipt_hash"]
    assert result["result"]["output"] == "node:hello node"

    continuity_log = tmp_path / "continuity.jsonl"
    entries = [json.loads(line) for line in continuity_log.read_text(encoding="utf-8").splitlines()]
    receipt_entries = [entry for entry in entries if entry.get("entry_type") == "nodeExecutionReceipt"]
    assert len(receipt_entries) == 1
    assert receipt_entries[0]["trace_id"] == submit["trace_id"]
    assert [entry.get("kind") for entry in entries if entry.get("kind")] == ["submit", "result"]


def test_node_v0_vetoes_payloads_that_exceed_policy_limit(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("NOVA_NODE_MAX_PAYLOAD_BYTES", "20")
    monkeypatch.setattr(nova_api, "build_provider", lambda config: object())

    client = TestClient(nova_api.app)
    response = client.post(
        "/node/submit",
        json={
            "task_id": "task-large",
            "intent": "chat",
            "caller_id": "cursor",
            "payload": {"prompt": "this payload is deliberately too large"},
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["decision"] == "blocked"
    assert payload["error"]["reason"] == "payload-too-large"
