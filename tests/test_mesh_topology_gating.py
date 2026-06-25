"""Mesh topology and gossip daemon gating (no example peers by default)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from flask import Flask

from src.mesh import gossip_runtime
from src.mesh.api_routes import register_mesh_routes
from src.mesh.runtime import configure_mesh_dir
from src.mesh.topology import (
    _load_deploy_peers,
    configured_peer_count,
    load_mesh_config,
    mesh_enabled,
    save_mesh_config,
)


class TestMeshTopologyGating(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="mesh-topo-gate-"))
        configure_mesh_dir(self.temp_root)
        self._env_patch = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()

    def tearDown(self):
        self._env_patch.stop()
        configure_mesh_dir(None)
        gossip_runtime.stop_gossip_daemon()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_example_peers_not_loaded_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            peers = _load_deploy_peers()
        urls = [p.get("url") if isinstance(p, dict) else p for p in peers]
        self.assertNotIn("http://127.0.0.1:5000", urls)
        self.assertNotIn("http://127.0.0.1:5001", urls)

    def test_example_peers_when_opt_in(self):
        with mock.patch.dict(os.environ, {"AAIS_MESH_USE_EXAMPLE_PEERS": "1"}, clear=False):
            peers = _load_deploy_peers()
        urls = [p.get("url") if isinstance(p, dict) else p for p in peers]
        self.assertIn("http://127.0.0.1:5000", urls)

    def test_mesh_disabled_when_env_zero(self):
        with mock.patch.dict(os.environ, {"AAIS_MESH_ENABLED": "0"}, clear=False):
            self.assertFalse(mesh_enabled())

    def test_configured_peer_count_zero_without_peers(self):
        save_mesh_config({"peers": [], "seeds": []}, self.temp_root)
        with mock.patch.dict(os.environ, {"AAIS_MESH_USE_EXAMPLE_PEERS": "0"}, clear=False):
            self.assertEqual(configured_peer_count(self.temp_root), 0)

    def test_gossip_daemon_not_started_when_mesh_disabled(self):
        gossip_runtime._DAEMON_THREAD = None
        gossip_runtime._DAEMON_STOP.clear()
        save_mesh_config({"peers": [], "gossip_interval_sec": 5}, self.temp_root)
        with mock.patch.dict(os.environ, {"AAIS_MESH_ENABLED": "0"}, clear=False):
            app = Flask(__name__)
            register_mesh_routes(app)
        self.assertIsNone(gossip_runtime._DAEMON_THREAD)

    def test_mesh_not_enabled_by_peers_json_file_alone(self):
        deploy_mesh = Path(__file__).resolve().parents[1] / "deploy" / "mesh"
        peers_file = deploy_mesh / "peers.json"
        had_file = peers_file.exists()
        backup = None
        if had_file:
            backup = peers_file.read_text(encoding="utf-8")
        try:
            deploy_mesh.mkdir(parents=True, exist_ok=True)
            peers_file.write_text(
                '[{"url": "http://127.0.0.1:5000"}, {"url": "http://127.0.0.1:5001"}]',
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertFalse(mesh_enabled())
        finally:
            if backup is not None:
                peers_file.write_text(backup, encoding="utf-8")
            elif peers_file.exists() and not had_file:
                peers_file.unlink()

    def test_load_mesh_config_ignores_deploy_peers_when_mesh_disabled(self):
        save_mesh_config({"peers": [], "seeds": []}, self.temp_root)
        with mock.patch.dict(
            os.environ,
            {"AAIS_MESH_ENABLED": "0", "AAIS_MESH_USE_EXAMPLE_PEERS": "0"},
            clear=False,
        ):
            cfg = load_mesh_config(self.temp_root)
        self.assertEqual(cfg.get("peers"), [])

    def test_gossip_run_noop_when_mesh_disabled(self):
        save_mesh_config({"peers": [], "gossip_interval_sec": 5}, self.temp_root)
        with mock.patch.dict(os.environ, {"AAIS_MESH_ENABLED": "0"}, clear=False):
            app = Flask(__name__)
            register_mesh_routes(app)
            client = app.test_client()
            resp = client.post("/api/mesh/gossip/run")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertFalse(body.get("mesh_enabled"))
        self.assertEqual(body.get("results"), [])

    def test_mesh_health_reports_disabled(self):
        save_mesh_config({"peers": [], "gossip_interval_sec": 5}, self.temp_root)
        with mock.patch.dict(os.environ, {"AAIS_MESH_ENABLED": "0"}, clear=False):
            app = Flask(__name__)
            register_mesh_routes(app)
            resp = app.test_client().get("/api/mesh/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertFalse(body.get("mesh_enabled"))
        self.assertEqual(body.get("configured_peer_count"), 0)


if __name__ == "__main__":
    unittest.main()
