"""Live federation: AAIS mesh (Flask) + rex-node (Flask) over threaded HTTP."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
REX_ROOT = ROOT.parent / "reasoning-exchange-node"
sys.path.insert(0, str(ROOT))

from flask import Flask

from src.mesh.api_routes import register_mesh_routes
from src.mesh.gossip import gossip_pull
from src.mesh.identity import load_or_create_identity
from src.mesh.invariants import InvariantStore
from src.mesh.known_peers import KnownPeersStore
from src.mesh.runtime import configure_mesh_dir
from src.mesh.topology import load_mesh_config, save_mesh_config

sys.path.insert(0, str(REX_ROOT))
from app import create_app as create_rex_app
from mesh.gossip import gossip_pull as rex_gossip_pull
from mesh.identity import load_or_create_identity as rex_load_identity
from mesh.invariants import InvariantStore as RexInvariantStore
from mesh.known_peers import KnownPeersStore as RexKnownPeersStore
from mesh.topology import load_mesh_config as rex_load_mesh_config
from mesh.topology import save_mesh_config as rex_save_mesh_config


def _wait_http(url: str, timeout: float = 5.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except (urllib.error.URLError, OSError):
            time.sleep(0.05)
    raise TimeoutError(f"server not ready: {url}")


class MeshFederationLiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_a = tempfile.TemporaryDirectory()
        self._tmp_b = tempfile.TemporaryDirectory()
        self.temp_a = Path(self._tmp_a.name)
        self.temp_b = Path(self._tmp_b.name)

        configure_mesh_dir(str(self.temp_a))
        self.identity_a = load_or_create_identity(str(self.temp_a))
        save_mesh_config(
            {
                "listen_port": 0,
                "base_url": "http://127.0.0.1:18001",
                "peers": [{"node_id": "rex-b", "base_url": "http://127.0.0.1:18002"}],
            },
            str(self.temp_a),
        )

        self.identity_b = rex_load_identity(str(self.temp_b))
        rex_save_mesh_config(
            {
                "listen_port": 0,
                "base_url": "http://127.0.0.1:18002",
                "peers": [{"node_id": self.identity_a["node_id"], "base_url": "http://127.0.0.1:18001"}],
            },
            str(self.temp_b),
        )

        app_a = Flask("aais-mesh-a")
        register_mesh_routes(app_a)
        self._server_a = make_server("127.0.0.1", 18001, app_a, threaded=True)
        self._thread_a = threading.Thread(target=self._server_a.serve_forever, daemon=True)
        self._thread_a.start()

        app_b = create_rex_app(str(self.temp_b), start_gossip=False)
        self._server_b = make_server("127.0.0.1", 18002, app_b, threaded=True)
        self._thread_b = threading.Thread(target=self._server_b.serve_forever, daemon=True)
        self._thread_b.start()

        _wait_http("http://127.0.0.1:18001/api/mesh/health")
        _wait_http("http://127.0.0.1:18002/api/mesh/health")

    def tearDown(self) -> None:
        self._server_a.shutdown()
        self._server_b.shutdown()
        configure_mesh_dir(None)
        self._tmp_a.cleanup()
        self._tmp_b.cleanup()

    def test_handshake_and_gossip_pull_registers_peers(self) -> None:
        result = gossip_pull(
            str(self.temp_a),
            self.identity_a,
            load_mesh_config(str(self.temp_a)),
            "http://127.0.0.1:18002",
        )
        self.assertTrue(result.get("ok"), result)

        store_a = KnownPeersStore(str(self.temp_a))
        store_b = RexKnownPeersStore(str(self.temp_b))
        self.assertTrue(store_a.is_known(self.identity_b["node_id"]))
        self.assertTrue(store_b.is_known(self.identity_a["node_id"]))

    def test_falsity_propagates_from_rex_to_aais(self) -> None:
        gossip_pull(
            str(self.temp_a),
            self.identity_a,
            load_mesh_config(str(self.temp_a)),
            "http://127.0.0.1:18002",
        )

        import urllib.request

        payload = {
            "push_entries": [
                {
                    "claim_fingerprint": "fed-live-fp-001",
                    "claim_text": "federated falsity live test",
                    "status": "refuted",
                    "confidence": 0.95,
                    "source_node_id": self.identity_b["node_id"],
                }
            ],
        }
        req = urllib.request.Request(
            "http://127.0.0.1:18001/api/mesh/gossip",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Mesh-Peer-Id": self.identity_b["node_id"],
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
        self.assertIn("falsity_head", body)

        from src.mesh.falsity_adapter import FalsityMeshAdapter

        adapter = FalsityMeshAdapter(str(self.temp_a))
        self.assertTrue(adapter.is_falsified("federated falsity live test"))
        self.assertIsNotNone(adapter.registry.is_falsified_fingerprint("fed-live-fp-001"))

    def test_invariant_merge_adopts_remote_bundle(self) -> None:
        RexInvariantStore(str(self.temp_b)).save(
            {
                "bundle_id": "inv-fed-live-1",
                "version": "1.0",
                "rules": [{"id": "no-empty-claim", "severity": "block"}],
            }
        )
        rex_gossip_pull(
            str(self.temp_b),
            self.identity_b,
            rex_load_mesh_config(str(self.temp_b)),
            "http://127.0.0.1:18001",
        )
        gossip_pull(
            str(self.temp_a),
            self.identity_a,
            load_mesh_config(str(self.temp_a)),
            "http://127.0.0.1:18002",
        )

        import urllib.request

        payload = {
            "invariants": {
                "bundle_id": "inv-fed-live-1",
                "version": "2.0",
                "rules": [
                    {"id": "no-empty-claim", "severity": "block"},
                    {"id": "require-source", "severity": "warn"},
                ],
            },
        }
        req = urllib.request.Request(
            "http://127.0.0.1:18001/api/mesh/gossip",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Mesh-Peer-Id": self.identity_b["node_id"],
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)

        merged = InvariantStore(str(self.temp_a)).load()
        rules = merged.get("rules") or []
        rule_ids = {r.get("id") for r in rules if isinstance(r, dict)}
        self.assertIn("require-source", rule_ids)


if __name__ == "__main__":
    unittest.main()
