from __future__ import annotations

import json


def test_node_identity_has_id_operator_and_policy_hash(tmp_path, monkeypatch) -> None:
    from nova.node.identity import NodeIdentity

    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(json.dumps({"version": "1.0"}), encoding="utf-8")
    monkeypatch.setenv("NOVA_NODE_ID", "jonai-node-test")
    monkeypatch.setenv("NOVA_OPERATOR_ID", "jon-halstead")
    monkeypatch.setenv("NOVA_OPERATOR_KEY_ID", "operator-key-test")

    ident = NodeIdentity.load(str(policy_path))

    assert ident.node_id.startswith("jonai-node-")
    assert ident.operator_id == "jon-halstead"
    assert ident.operator_key_id == "operator-key-test"
    assert len(ident.policy_hash) == 64
