"""Live UGR mesh health polling for operator console."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from src.datetime_compat import UTC
from typing import Any

from src.ugr.cloud.clients import UGRMeshClients
from src.ugr.cloud.mesh_config import deployment_mode, load_mesh_config


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _mesh_poll_timeout(requested: float | None = None) -> float:
    if requested is not None:
        return requested
    mode = deployment_mode()
    if mode in {"monolith", "local", "mock"}:
        return 0.75
    return 2.0


def _poll_one_service(clients: UGRMeshClients, mesh: Any, name: str) -> dict[str, Any]:
    try:
        health = clients.health(name)
        status = str(health.get("status") or "ok")
        return {
            "name": name,
            "status": "ok" if status == "ok" else "degraded",
            "base_url": mesh.base_url(name),
            "health": health,
        }
    except Exception as exc:
        return {
            "name": name,
            "status": "unreachable",
            "base_url": mesh.base_url(name),
            "error": str(exc),
        }


def poll_mesh_health(*, timeout: float | None = None) -> dict[str, Any]:
    """Poll configured mesh services; advisory only (no side effects)."""
    mesh = load_mesh_config()
    mode = deployment_mode()
    poll_timeout = _mesh_poll_timeout(timeout)
    clients = UGRMeshClients(mesh=mesh, timeout=poll_timeout)
    service_names = sorted(mesh.services.keys())
    services: list[dict[str, Any]] = []
    workers = min(8, max(1, len(service_names)))
    if workers > 1 and os.getenv("UGR_MESH_POLL_SERIAL", "").strip().lower() not in {"1", "true", "yes"}:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_poll_one_service, clients, mesh, name): name for name in service_names}
            for fut in as_completed(futures):
                services.append(fut.result())
        services.sort(key=lambda item: str(item.get("name") or ""))
    else:
        for name in service_names:
            services.append(_poll_one_service(clients, mesh, name))

    healthy = sum(1 for item in services if item.get("status") == "ok")
    total = len(services)
    if healthy == total and total > 0:
        poll_status = "ok"
    elif healthy > 0:
        poll_status = "partial"
    else:
        poll_status = "unreachable"

    return {
        "polled_at_utc": _utc_now_iso(),
        "deployment_mode": mode,
        "cluster_id": mesh.cluster_id,
        "poll_status": poll_status,
        "healthy_count": healthy,
        "total_count": total,
        "services": services,
        "runtime_effect": "readout_only",
        "claim_status": "proven" if poll_status == "ok" else "asserted",
    }
