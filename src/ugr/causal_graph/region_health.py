"""Region health overlays for causal graph v1."""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
import json
import os
from pathlib import Path
from typing import Any

from src.ugr.platform.tenant_registry import normalize_tenant_id


def _default_regions_path() -> Path:
    env_path = os.getenv("UGR_REGIONS_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "regions.json"


class RegionHealthRegistry:
    """Region health and tenant overlay routing metadata."""

    def __init__(self, config_path: str | Path | None = None):
        self.path = Path(config_path) if config_path else _default_regions_path()
        self._payload = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"regions": {}}

    @property
    def default_region(self) -> str:
        return str(self._payload.get("default_region") or "local-primary")

    def list_regions(self) -> list[dict[str, Any]]:
        regions = dict(self._payload.get("regions") or {})
        return [{"region_id": region_id, **dict(spec)} for region_id, spec in regions.items()]

    def get(self, region_id: str) -> dict[str, Any] | None:
        spec = dict(self._payload.get("regions") or {}).get(str(region_id or ""))
        if not spec:
            return None
        return _wrap_ul_payload({"region_id": region_id, **spec})

    def resolve_region_for_tenant(self, tenant_scope: str | None) -> str:
        normalized = normalize_tenant_id(tenant_scope or "global")
        for region_id, spec in dict(self._payload.get("regions") or {}).items():
            overlays = [normalize_tenant_id(item) for item in list(spec.get("overlay_tenants") or [])]
            if normalized in overlays:
                return str(region_id)
        return self.default_region

    def health_snapshot(self) -> dict[str, Any]:
        regions = self.list_regions()
        healthy = sum(1 for region in regions if str(region.get("status") or "") == "healthy")
        return _wrap_ul_payload({
            "default_region": self.default_region,
            "region_count": len(regions),
            "healthy_regions": healthy,
            "degraded_regions": len(regions) - healthy,
            "regions": regions,
        })

    def overlay_for_query(self, *, tenant_scope: str | None = None, region_id: str | None = None) -> dict[str, Any]:
        resolved = str(region_id or self.resolve_region_for_tenant(tenant_scope))
        spec = self.get(resolved) or {"region_id": resolved, "status": "unknown"}
        return _wrap_ul_payload({
            "region_id": resolved,
            "status": spec.get("status"),
            "shard_ids": list(spec.get("shard_ids") or []),
            "overlay_tenants": list(spec.get("overlay_tenants") or []),
            "latency_bias": spec.get("latency_bias"),
        })
