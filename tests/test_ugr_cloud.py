"""Tests for UGR Phase 2 cloud mesh."""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from werkzeug.serving import make_server

from src.cognitive_bridge import CognitiveBridgeService
from src.immune_system import ImmuneSystemController
from src.jarvis_detachment_guard import JarvisDetachmentGuard
from src.module_governance import module_governance
from src.phase_gate import reset_registry
from src.ugr.cloud.clients import UGRMeshClients
from src.ugr.cloud.distributed_runtime import DistributedUnifiedGovernedRuntime
from src.ugr.cloud.mesh_config import UGRMeshConfig, load_mesh_config
from src.ugr.cloud.services import (
    create_convergence_app,
    create_lane_worker_app,
    create_ledger_app,
    create_orchestrator_app,
    create_policy_app,
)
from src.ugr.unified_runtime import UnifiedGovernedRuntime

REPO_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _ServiceThread:
    def __init__(self, app, port: int):
        self.server = make_server("127.0.0.1", port, app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()


class TestUGRCloudMesh(unittest.TestCase):
    def test_load_default_mesh_config(self):
        mesh = load_mesh_config()
        self.assertIn("orchestrator", mesh.services)
        self.assertEqual(mesh.base_url("policy").startswith("http://"), True)

    def test_manifest_validator_passes(self):
        result = subprocess.run(
            [sys.executable, "wolf-cog-os/scripts/validate-ugr-cloud-manifest.py", "--mode", "fail"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, (result.stdout or "") + (result.stderr or ""))


class TestUGRDistributedCluster(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-cloud-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        self.original_mode = os.environ.get("UGR_DEPLOYMENT_MODE")
        os.environ["UGR_DEPLOYMENT_MODE"] = "distributed"
        self.original_mesh = os.environ.get("UGR_MESH_CONFIG")
        self.ports = {name: _free_port() for name in ("orchestrator", "policy", "ledger", "lane_worker", "convergence")}
        mesh_path = self.temp_root / "mesh.json"
        mesh_path.write_text(
            json.dumps(
                {
                    "mesh_version": "0.1",
                    "cluster_id": "test-cluster",
                    "services": {
                        name: {"host": "127.0.0.1", "port": port, "role": name}
                        for name, port in self.ports.items()
                    },
                }
            ),
            encoding="utf-8",
        )
        os.environ["UGR_MESH_CONFIG"] = str(mesh_path)
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        module_governance.configure_runtime_dir(self.temp_root)
        module_governance.reset()
        reset_registry()
        bridge = CognitiveBridgeService(
            immune_controller=ImmuneSystemController(runtime_dir=self.temp_root),
            detachment_guard=JarvisDetachmentGuard(runtime_dir=self.temp_root),
        )
        self.servers = [
            _ServiceThread(create_policy_app(bridge), self.ports["policy"]),
            _ServiceThread(create_ledger_app(), self.ports["ledger"]),
            _ServiceThread(create_lane_worker_app(), self.ports["lane_worker"]),
            _ServiceThread(create_convergence_app(), self.ports["convergence"]),
        ]
        self.runtime = DistributedUnifiedGovernedRuntime(
            clients=UGRMeshClients(mesh=load_mesh_config(mesh_path)),
            runtime_dir=self.temp_root,
        )
        self.servers.append(_ServiceThread(create_orchestrator_app(self.runtime), self.ports["orchestrator"]))
        for server in self.servers:
            server.start()

    def tearDown(self):
        for server in reversed(self.servers):
            server.stop()
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        module_governance.reset()
        reset_registry()
        if self.original_mode is None:
            os.environ.pop("UGR_DEPLOYMENT_MODE", None)
        else:
            os.environ["UGR_DEPLOYMENT_MODE"] = self.original_mode
        if self.original_mesh is None:
            os.environ.pop("UGR_MESH_CONFIG", None)
        else:
            os.environ["UGR_MESH_CONFIG"] = self.original_mesh
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_distributed_deliberation_matches_monolith_beliefs(self):
        request = {
            "question": "What likely caused the runtime latency spike?",
            "intent": "diagnose_runtime",
            "tenant_id": "default",
            "context": {"component": "orchestrator"},
            "lane_types": ["symbolic", "graph", "llm"],
        }

        def belief_signature(result):
            return sorted(
                (
                    item.get("subject"),
                    item.get("predicate"),
                    item.get("object"),
                    item.get("status"),
                )
                for item in (result.get("convergence") or {}).get("final_beliefs") or []
            )

        monolith = UnifiedGovernedRuntime(
            bridge=CognitiveBridgeService(
                immune_controller=ImmuneSystemController(runtime_dir=self.temp_root),
                detachment_guard=JarvisDetachmentGuard(runtime_dir=self.temp_root),
            ),
            runtime_dir=self.temp_root,
        )
        mono_result = monolith.handle_request(request)
        dist_result = self.runtime.handle_request(request)
        self.assertEqual(mono_result["status"], "ok")
        self.assertEqual(dist_result["status"], "ok")
        self.assertEqual(dist_result.get("deployment_mode"), "distributed")
        self.assertEqual(
            belief_signature(mono_result),
            belief_signature(dist_result),
        )

    def test_mesh_clients_health(self):
        clients = UGRMeshClients(mesh=load_mesh_config())
        for service in ("policy", "ledger", "lane_worker", "convergence"):
            health = clients.health(service)
            self.assertEqual(health.get("status"), "ok")


if __name__ == "__main__":
    unittest.main()
