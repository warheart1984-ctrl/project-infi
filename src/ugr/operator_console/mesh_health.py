"""Live UGR mesh health polling for operator console."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
from typing import Any

from src.ugr.cloud.clients import UGRMeshClients
from src.ugr.cloud.mesh_config import deployment_mode, load_mesh_config


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def poll_mesh_health(*, timeout: float = 2.0) -> dict[str, Any]:
    """Poll configured mesh services; advisory only (no side effects)."""
    mesh = load_mesh_config()
    mode = deployment_mode()
    clients = UGRMeshClients(mesh=mesh, timeout=timeout)
    services: list[dict[str, Any]] = []

    for name in sorted(mesh.services.keys()):
        try:
            health = clients.health(name)
            status = str(health.get("status") or "ok")
            services.append(
                {
                    "name": name,
                    "status": "ok" if status == "ok" else "degraded",
                    "base_url": mesh.base_url(name),
                    "health": health,
                }
            )
        except Exception as exc:
            services.append(
                {
                    "name": name,
                    "status": "unreachable",
                    "base_url": mesh.base_url(name),
                    "error": str(exc),
                }
            )

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
