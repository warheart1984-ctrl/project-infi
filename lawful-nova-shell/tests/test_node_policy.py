from __future__ import annotations


def test_node_policy_blocks_banned_intent(monkeypatch) -> None:
    from nova.node.policy import GovernanceRuntime

    runtime = GovernanceRuntime()
    runtime.policy["safety"]["banned_intents"] = ["blocked-intent"]

    decision = runtime.enforce_invariants({"intent": "blocked-intent"})

    assert decision["decision"] == "blocked"
    assert decision["reason"] == "banned-intent"
    assert decision["policy_version"] == "1.0"


def test_node_policy_allows_bounded_payload(monkeypatch) -> None:
    from nova.node.policy import GovernanceRuntime

    monkeypatch.setenv("NOVA_NODE_MAX_PAYLOAD_BYTES", "1000")
    runtime = GovernanceRuntime()

    decision = runtime.enforce_invariants({"intent": "chat", "payload": {"prompt": "hello"}})

    assert decision["decision"] == "allowed"
    assert "continuity" in decision["receipts"]
    assert decision["trace_id"].startswith("trace-")


def test_canonical_policy_manifest_loads_node_identity() -> None:
    from pathlib import Path
    from nova.node.identity import NodeIdentity
    from nova.node.policy import GovernanceRuntime

    policy_path = Path(__file__).resolve().parents[1] / "policy.yaml"

    runtime = GovernanceRuntime(str(policy_path))
    identity = NodeIdentity.load(str(policy_path))

    assert runtime.policy["version"] == "1.0"
    assert runtime.policy["operator_id"] == "jon-halstead"
    assert identity.node_id == "jonai-node-001"
    assert identity.operator_id == "jon-halstead"
    assert len(identity.policy_hash) == 64


def test_rate_limit_blocks_repeated_calls(tmp_path, monkeypatch) -> None:
    from nova.node.policy import GovernanceRuntime

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    runtime = GovernanceRuntime()
    runtime.policy["safety"]["rate_limits"] = {
        "per_user_per_minute": 1,
        "per_user_per_hour": 2,
    }

    first = runtime.enforce_invariants({"caller_id": "cursor", "intent": "chat"})
    second = runtime.enforce_invariants({"caller_id": "cursor", "intent": "chat"})

    assert first["decision"] == "allowed"
    assert second["decision"] == "blocked"
    assert second["reason"] == "rate-limit-exceeded"
    assert second["rate_limit"]["per_user_per_minute"] == 1


def test_rate_limit_counters_are_exposed(tmp_path, monkeypatch) -> None:
    from nova.node.policy import GovernanceRuntime, get_rate_limit_state

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    runtime = GovernanceRuntime()
    runtime.policy["safety"]["rate_limits"] = {
        "per_user_per_minute": 10,
        "per_user_per_hour": 10,
    }
    runtime.enforce_invariants({"caller_id": "operator-1", "intent": "chat"})

    state = get_rate_limit_state()

    assert state["limits"]["per_user_per_minute"] == 10
    assert state["callers"]["operator-1"]["minute_count"] == 1
