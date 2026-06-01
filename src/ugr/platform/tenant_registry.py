"""Tenant registry and overlay policy for UGR Phase 4."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


def _default_tenants_path() -> Path:
    env_path = os.getenv("UGR_TENANTS_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "tenants.json"


def normalize_tenant_id(value: Any) -> str:
    raw = str(value or "default").strip().lower()
    if raw in {"", "default", "global"}:
        return "global"
    if raw.startswith("tenant:"):
        return raw
    return f"tenant:{raw}"


@dataclass(frozen=True)
class TenantSpec:
    tenant_id: str
    label: str
    enabled: bool
    shard_id: str
    overlay_global: bool
    max_claims_per_query: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "label": self.label,
            "enabled": self.enabled,
            "shard_id": self.shard_id,
            "overlay_global": self.overlay_global,
            "max_claims_per_query": self.max_claims_per_query,
        }


class TenantRegistry:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else _default_tenants_path()
        self._payload = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"tenants": {}}

    def get(self, tenant_id: str) -> TenantSpec | None:
        normalized = normalize_tenant_id(tenant_id)
        spec = dict(self._payload.get("tenants") or {}).get(normalized) or dict(
            self._payload.get("tenants") or {}
        ).get("global")
        if not spec:
            return None
        return TenantSpec(
            tenant_id=normalized,
            label=str(spec.get("label") or normalized),
            enabled=bool(spec.get("enabled", True)),
            shard_id=str(spec.get("shard_id") or normalized.replace(":", "-")),
            overlay_global=bool(spec.get("overlay_global", True)),
            max_claims_per_query=int(spec.get("max_claims_per_query") or 50),
        )

    def list_tenants(self) -> list[TenantSpec]:
        tenants: list[TenantSpec] = []
        for tenant_id in dict(self._payload.get("tenants") or {}).keys():
            spec = self.get(tenant_id)
            if spec:
                tenants.append(spec)
        return tenants
