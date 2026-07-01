from __future__ import annotations

import pytest


def test_agent_registry_preserves_color_team_roles_and_capability_gate() -> None:
    from nova.node.agent_manifest import CapabilityGate, default_agent_registry

    registry = default_agent_registry()

    coder = registry.get("agent-coder")
    reviewer = registry.get("agent-reviewer")
    security = registry.get("agent-security")
    sentinel = registry.get("agent-sentinel")

    assert coder.role == "blue_team_builder"
    assert coder.color == "blue"
    assert coder.can_write_files is True
    assert coder.can_modify_deps is True
    assert "write_patches" in coder.capabilities
    assert reviewer.role == "red_team_inspector"
    assert security.role == "purple_team_security"
    assert sentinel.role == "orange_team_governance_enforcer"

    gate = CapabilityGate(registry, policy_version="1.0")
    receipt = gate.authorize(
        "agent-coder",
        "write_files",
        {"trace_id": "trace-agent-1", "file_path": "src/app.py"},
    )

    assert receipt.agent_id == "agent-coder"
    assert receipt.action == "write_files"
    assert receipt.trace_id == "trace-agent-1"
    assert receipt.compute_output_hash({"ok": True}).startswith("sha256:")

    with pytest.raises(PermissionError, match="agent-reviewer cannot write files"):
        gate.authorize("agent-reviewer", "write_files", {"trace_id": "trace-agent-2"})


def test_agent_manifest_routes_expose_agents_and_planned_tools(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    client = TestClient(nova_api.app)
    agents = client.get("/node/agents").json()
    tool_manifest = client.get("/node/agent-tools").json()

    assert agents["agents"]["coder"]["id"] == "agent-coder"
    assert agents["agents"]["wiring"]["role"] == "green_team_integrator"
    assert agents["agents"]["sentinel"]["governance"]["can_block_actions"] is True
    assert agents["orchestration"]["status"] == "manifest_only"
    assert "Tools remain stateless Ring-2 invocations" in agents["orchestration"]["guardrail"]

    names = [tool["name"] for tool in tool_manifest["tools"]]
    assert "coder_tool" in names
    assert "rollback_tool" in names
    coder_tool = next(tool for tool in tool_manifest["tools"] if tool["name"] == "coder_tool")
    rollback_tool = next(tool for tool in tool_manifest["tools"] if tool["name"] == "rollback_tool")
    assert coder_tool["owner_agent"] == "agent-coder"
    assert coder_tool["implemented"] is True
    assert rollback_tool["owner_agent"] == "agent-sentinel"
    assert rollback_tool["implemented"] is False


def test_node_tools_endpoint_includes_owner_agent_metadata(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    import nova.api as nova_api

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    client = TestClient(nova_api.app)
    tools = client.get("/node/tools").json()["tools"]

    code_tool = next(tool for tool in tools if tool["name"] == "code")
    wire_tool = next(tool for tool in tools if tool["name"] == "wire")
    assert code_tool["owner_agent"] == "agent-coder"
    assert code_tool["tool_manifest_name"] == "coder_tool"
    assert wire_tool["owner_agent"] == "agent-wiring"
    assert wire_tool["tool_manifest_name"] == "wiring_tool"
