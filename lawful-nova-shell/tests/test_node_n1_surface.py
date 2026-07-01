from __future__ import annotations


def test_status_lists_n1_upgrade_surface(tmp_path, monkeypatch) -> None:
    from nova.node.status import node_status

    monkeypatch.setenv("NOVA_NODE_RUNTIME_DIR", str(tmp_path))

    status = node_status()

    for endpoint in [
        "/node/replay/{trace_id}",
        "/node/continuity",
        "/node/policy",
        "/node/mesh",
        "/node/alerts",
        "/node/conformance/n0",
        "/node/conformance/n0/badge",
        "/node/evidence-bundle",
    ]:
        assert endpoint in status["endpoints"]
