"""API tests for AAIS mesh peer routes and evaluate hooks."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from flask import Flask

from src.mesh.api_routes import register_mesh_routes
from src.mesh.evaluate_hooks import check_mesh_peer_allowed
from src.mesh.falsity_adapter import FalsityMeshAdapter
from src.mesh.handshake import build_ack, build_hello
from src.mesh.identity import load_or_create_identity
from src.mesh.invariants import InvariantStore
from src.mesh.known_peers import KnownPeersStore
from src.mesh.runtime import configure_mesh_dir
from src.mesh.topology import save_mesh_config


def _remote_identity() -> dict:
    remote_root = Path(tempfile.mkdtemp(prefix="mesh-remote-identity-"))
    identity = load_or_create_identity(remote_root)
    shutil.rmtree(remote_root, ignore_errors=True)
    return identity


class TestMeshApi(unittest.TestCase):
    """Verify /api/mesh/* routes on an isolated Flask app."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="aais-mesh-api-"))
        configure_mesh_dir(self.temp_root)
        save_mesh_config({"node_name": "test-aais-mesh", "require_handshake": False}, self.temp_root)

        self.app = Flask(__name__)
        register_mesh_routes(self.app)
        self.client = self.app.test_client()

    def tearDown(self):
        configure_mesh_dir(None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_mesh_identity(self):
        response = self.client.get("/api/mesh/identity")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("node_id", payload)
        self.assertIn("fingerprint", payload)
        self.assertIn("verify_key", payload)
        self.assertEqual(payload["node_name"], "test-aais-mesh")

    def test_handshake_round_trip(self):
        remote = _remote_identity()
        ledger = FalsityMeshAdapter(self.temp_root)
        invariants = InvariantStore(self.temp_root)
        config = {"node_name": "remote", "capabilities": ["handshake", "falsity_sync"]}

        hello = build_hello(
            remote,
            config,
            falsity_head=ledger.head_hash(),
            invariant_digest=invariants.digest(),
        )
        challenge_response = self.client.post("/api/mesh/handshake", json=hello)
        self.assertEqual(challenge_response.status_code, 200)
        challenge = challenge_response.get_json()
        self.assertEqual(challenge.get("phase"), "CHALLENGE")
        self.assertTrue(challenge.get("nonce"))

        ack = build_ack(remote, challenge["nonce"])
        ack_response = self.client.post("/api/mesh/handshake/ack", json=ack)
        self.assertEqual(ack_response.status_code, 200)
        result = ack_response.get_json()
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("peer_node_id"), remote["node_id"])

        known = KnownPeersStore(self.temp_root)
        self.assertTrue(known.is_known(remote["node_id"]))

    def test_handshake_rejects_bad_signature(self):
        remote = _remote_identity()
        invariants = InvariantStore(self.temp_root)
        ledger = FalsityMeshAdapter(self.temp_root)
        config = {"capabilities": ["handshake"]}

        hello = build_hello(
            remote,
            config,
            falsity_head=ledger.head_hash(),
            invariant_digest=invariants.digest(),
        )
        challenge = self.client.post("/api/mesh/handshake", json=hello).get_json()
        ack = build_ack(remote, challenge["nonce"])
        ack["signature"] = "0" * 64

        result = self.client.post("/api/mesh/handshake/ack", json=ack).get_json()
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason"), "invalid_signature")

    def test_gossip_merge_push_entries(self):
        fingerprint = "abc123" + "0" * 58
        entry = {
            "claim_fingerprint": fingerprint,
            "claim_hash": fingerprint,
            "claim": "Rejected mesh claim",
            "reason": "rls_rejected",
            "source_node": "peer-test",
            "recorded_at": "2026-06-08T12:00:00+00:00",
        }
        response = self.client.post(
            "/api/mesh/gossip",
            json={"falsity_head": None, "push_entries": [entry]},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("falsity_head", payload)
        self.assertIn("falsity_entries", payload)

        ledger = FalsityMeshAdapter(self.temp_root)
        exported = ledger.export_since_head(None)
        fps = {e.get("claim_fingerprint") or e.get("claim_hash") for e in exported}
        self.assertIn(fingerprint, fps)

    def test_mesh_invariants_export(self):
        response = self.client.get("/api/mesh/invariants")
        self.assertEqual(response.status_code, 200)
        bundle = response.get_json()
        self.assertIn("rules", bundle)
        self.assertIn("bundle_id", bundle)
        rule_ids = {r.get("id") for r in bundle.get("rules", [])}
        self.assertIn("min_confidence", rule_ids)

    def test_require_handshake_blocks_unknown_peer(self):
        save_mesh_config({"require_handshake": True}, self.temp_root)
        allowed, reason = check_mesh_peer_allowed(str(uuid.uuid4()), str(self.temp_root))
        self.assertFalse(allowed)
        self.assertEqual(reason, "mesh_peer_not_handshaken")

        remote = _remote_identity()
        KnownPeersStore(self.temp_root).register(
            remote["node_id"],
            fingerprint="fp",
            capabilities=["reasoning_evaluate", "falsity_sync"],
        )
        allowed, reason = check_mesh_peer_allowed(remote["node_id"], str(self.temp_root))
        self.assertTrue(allowed)
        self.assertIsNone(reason)


class TestMeshEvaluateIntegration(unittest.TestCase):
    """Mesh evaluate hook against full AAIS app when import succeeds."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="aais-mesh-eval-"))
        configure_mesh_dir(self.temp_root)
        save_mesh_config({"require_handshake": True}, self.temp_root)

    def tearDown(self):
        configure_mesh_dir(None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_evaluate_rejects_unknown_mesh_peer(self):
        import src.api as api
        from src.phase_gate import reset_registry

        original_governance = api.module_governance.runtime_dir
        original_immune = api.immune_system.runtime_dir
        original_detachment = api.cognitive_bridge_service.detachment_guard.runtime_dir
        api.module_governance.configure_runtime_dir(self.temp_root)
        api.module_governance.reset()
        api.immune_system.configure_runtime_dir(self.temp_root)
        api.immune_system.reset()
        api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(self.temp_root)
        api.cognitive_bridge_service.detachment_guard.reset()
        reset_registry()

        try:
            packet = {
                "version": "1.0",
                "type": "reasoning_packet",
                "id": str(uuid.uuid4()),
                "timestamp": "2026-04-25T14:00:00Z",
                "payload": {
                    "claim": "Mesh peer test claim.",
                    "reasoning": "Testing require_handshake on evaluate.",
                    "evidence": ["mesh"],
                    "confidence": 0.84,
                },
                "meta": {"source": "mesh_test", "domain": "test", "tags": []},
            }
            with api.app.test_client() as client:
                response = client.post(
                    "/api/reasoning/evaluate",
                    json=packet,
                    headers={"X-Mesh-Peer-Id": str(uuid.uuid4())},
                )
            self.assertEqual(response.status_code, 403)
            body = response.get_json()
            self.assertEqual(body.get("status"), "REJECT")
            self.assertEqual(body.get("reason"), "mesh_peer_not_handshaken")
            self.assertEqual(body.get("source"), "mesh")
        finally:
            api.module_governance.configure_runtime_dir(original_governance)
            api.module_governance.reset()
            api.immune_system.configure_runtime_dir(original_immune)
            api.immune_system.reset()
            api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(original_detachment)
            api.cognitive_bridge_service.detachment_guard.reset()
            reset_registry()


if __name__ == "__main__":
    unittest.main()
