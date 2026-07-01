from __future__ import annotations


def test_node_status_exposes_receipts_and_ledger_endpoints(tmp_path, monkeypatch) -> None:
    from nova.node.status import node_status

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("NOVA_NODE_ID", "jonai-node-status")

    status = node_status()

    assert status["node_id"] == "jonai-node-status"
    assert "/node/receipts" in status["endpoints"]
    assert "/node/ledger" in status["endpoints"]
    assert "/node/gossip" in status["endpoints"]
    assert "/node/hello" in status["endpoints"]
    assert "rate_limits" in status
    assert "federation" in status
    assert "governance_health" in status
