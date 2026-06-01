"""UGR service mesh configuration."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


UGR_MESH_VERSION = "0.1"
DEFAULT_SERVICES = {
    "orchestrator": {"host": "127.0.0.1", "port": 8090, "role": "gateway"},
    "policy": {"host": "127.0.0.1", "port": 8091, "role": "policy_invariants"},
    "ledger": {"host": "127.0.0.1", "port": 8092, "role": "pattern_ledger"},
    "lane_worker": {"host": "127.0.0.1", "port": 8093, "role": "mlca_lanes"},
    "convergence": {"host": "127.0.0.1", "port": 8094, "role": "convergence"},
    "ingestion": {"host": "127.0.0.1", "port": 8095, "role": "ingestion"},
    "platform": {"host": "127.0.0.1", "port": 8096, "role": "platform_scale"},
    "graph_index": {"host": "127.0.0.1", "port": 8097, "role": "graph_index"},
    "model_pool": {"host": "127.0.0.1", "port": 8098, "role": "model_pool"},
    "embryo_gateway": {"host": "127.0.0.1", "port": 8099, "role": "embryo_gateway"},
    "causal_graph": {"host": "127.0.0.1", "port": 8100, "role": "causal_graph"},
    "embryo_v1_gateway": {"host": "127.0.0.1", "port": 8101, "role": "embryo_v1_gateway"},
}


def _default_mesh_path() -> Path:
    env_path = os.getenv("UGR_MESH_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "deploy" / "ugr" / "mesh.local.json"


@dataclass(frozen=True)
class UGRMeshConfig:
    mesh_version: str
    cluster_id: str
    services: dict[str, dict[str, Any]]

    def base_url(self, service_name: str) -> str:
        spec = self.services.get(service_name) or {}
        host = str(spec.get("host") or "127.0.0.1")
        port = int(spec.get("port") or 0)
        if port <= 0:
            raise KeyError(f"service port missing for {service_name}")
        return f"http://{host}:{port}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mesh_version": self.mesh_version,
            "cluster_id": self.cluster_id,
            "services": self.services,
        }


def load_mesh_config(path: str | Path | None = None) -> UGRMeshConfig:
    mesh_path = Path(path) if path else _default_mesh_path()
    if mesh_path.exists():
        payload = json.loads(mesh_path.read_text(encoding="utf-8"))
    else:
        payload = {
            "mesh_version": UGR_MESH_VERSION,
            "cluster_id": "local-single-node",
            "services": DEFAULT_SERVICES,
        }
    services = dict(payload.get("services") or DEFAULT_SERVICES)
    return UGRMeshConfig(
        mesh_version=str(payload.get("mesh_version") or UGR_MESH_VERSION),
        cluster_id=str(payload.get("cluster_id") or "local-single-node"),
        services=services,
    )


def deployment_mode() -> str:
    return str(os.getenv("UGR_DEPLOYMENT_MODE") or "monolith").strip().lower()
