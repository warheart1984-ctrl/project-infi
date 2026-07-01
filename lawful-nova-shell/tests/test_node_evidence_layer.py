from __future__ import annotations

from pathlib import Path


class FakeProvider:
    provider_id = "local"
    model = "nova-local"

    def chat_completion(self, governed_request):
        text = governed_request["messages"][-1]["content"]
        return {
            "completion": {
                "id": f"completion-{text}",
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


def test_replay_continuity_policy_mesh_and_alert_routes(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api
    from nova.node.federation import receive_gossip_payload
    from nova.node.policy import GovernanceRuntime

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("NOVA_NODE_ID", "jonai-node-evidence")
    monkeypatch.setenv("NOVA_NODE_RATE_PER_MINUTE", "50")
    monkeypatch.setattr(nova_api, "build_provider", lambda config: FakeProvider())
    nova_api.app.state.node_provider_factory = lambda config: FakeProvider()

    client = TestClient(nova_api.app)
    submitted = client.post(
        "/node/submit",
        json={
            "task_id": "task-replay",
            "intent": "chat",
            "caller_id": "operator",
            "payload": {"messages": [{"role": "user", "content": "replay me"}]},
        },
    ).json()

    replayed = client.post(f"/node/replay/{submitted['trace_id']}").json()
    assert replayed["trace_id"] == submitted["trace_id"]
    assert replayed["original_output"] == {"output": "node:replay me", "completion_id": "completion-replay me"}
    assert replayed["replayed_output"]["output"] == "node:replay me"
    assert replayed["deterministic"] is True
    assert replayed["diff"]["type"] == "none"
    assert replayed["policy_version_original"] == replayed["policy_version_replayed"]

    continuity = client.get("/node/continuity?limit=10").json()
    assert any(event["kind"] == "submit" for event in continuity["events"])
    assert any(event["trace_id"] == submitted["trace_id"] for event in continuity["events"])

    policy = client.get("/node/policy").json()
    assert "current_policy" in policy
    assert policy["policy_hash"]
    assert set(policy["diff"]) == {"added", "removed", "changed"}

    receive_gossip_payload(
        {
            "summary": {
                "node_id": "peer-invalid",
                "policy_hash": "sha256:peer",
                "timestamp": 123,
            },
            "signature": "bad",
        }
    )
    mesh = client.get("/node/mesh").json()
    assert mesh["peers"][0]["node_id"] == "peer-invalid"
    assert mesh["peers"][0]["trust_level"] == "invalid"
    assert "peer-invalid" in mesh["divergent_peers"]

    runtime = GovernanceRuntime()
    runtime.enforce_invariants({"caller_id": "operator", "intent": "chat"})
    alerts = client.get("/node/alerts").json()
    assert any(alert["category"] == "federation" for alert in alerts["alerts"])
    assert "/node/alerts" in client.get("/node/status").json()["endpoints"]


def test_n0_badge_report_and_evidence_bundle(tmp_path, monkeypatch) -> None:
    from nova.node.ceb import generate_evidence_bundle
    from nova.node.conformance import generate_n0_badge, generate_n0_report
    from nova.node.continuity import append_event, append_receipt
    from nova.node.ledger import stable_hash

    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        "\n".join(
            [
                "version: '1.0'",
                "node_id: jonai-node-bundle",
                "operator_id: jon-halstead",
                "invariants:",
                "  boundedness:",
                "    max_tokens: 2048",
                "safety:",
                "  banned_intents: []",
                "  rate_limits:",
                "    per_user_per_minute: 10",
                "    per_user_per_hour: 100",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path / ".runtime" / "node"))
    monkeypatch.setenv("NOVA_NODE_ID", "jonai-node-bundle")

    append_event("submit", {"trace_id": "trace-bundle", "decision": {"decision": "allowed"}})
    append_receipt(
        {
            "entry_type": "nodeExecutionReceipt",
            "trace_id": "trace-bundle",
            "receipt_hash": "sha256:receipt",
            "receipt": {"trace_id": "trace-bundle", "policy_version": "1.0"},
        }
    )

    report = generate_n0_report(policy_path=str(policy_path))
    assert report["profile"] == "N0"
    assert report["verdict"]["conformant"] is True
    assert report["sections"]["identity_policy"][0]["pass"] is True

    badge = generate_n0_badge(report, policy_path=str(policy_path))
    assert badge["profile"] == "N0"
    assert badge["status"] == "conformant"
    assert badge["policy_hash"] == report["policy_hash"]
    assert badge["conformance_hash"] == stable_hash(report)

    bundle = generate_evidence_bundle(tmp_path / "bundle", report=report)
    assert Path(bundle["bundle_path"]).exists()
    assert bundle["manifest"]["version"] == "CEB-1.0"
    assert bundle["manifest"]["bundle_hash"].startswith("sha256:")
    assert any(item["path"] == "conformance/n0_report.json" for item in bundle["manifest"]["files"])


def test_conformance_and_bundle_routes(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path / ".runtime" / "node"))

    client = TestClient(nova_api.app)

    report = client.get("/node/conformance/n0").json()
    assert report["profile"] == "N0"
    badge = client.get("/node/conformance/n0/badge").json()
    assert badge["profile"] == "N0"
    assert badge["conformance_hash"]
    bundle = client.post("/node/evidence-bundle").json()
    assert bundle["manifest"]["version"] == "CEB-1.0"
    assert Path(bundle["bundle_path"]).exists()
