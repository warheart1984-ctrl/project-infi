"""Graph shard routing for sharded pattern ledger storage."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id


def _default_shards_path() -> Path:
    env_path = os.getenv("UGR_GRAPH_SHARDS_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "graph-shards.json"


@dataclass(frozen=True)
class GraphShardSpec:
    shard_id: str
    domain: str
    storage_backend: str
    enabled: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "shard_id": self.shard_id,
            "domain": self.domain,
            "storage_backend": self.storage_backend,
            "enabled": self.enabled,
        }


class GraphShardRouter:
    """Route tenant/domain requests to shard ids."""

    def __init__(
        self,
        *,
        shards_path: str | Path | None = None,
        tenants: TenantRegistry | None = None,
        runtime_root: str | Path | None = None,
    ):
        self.path = Path(shards_path) if shards_path else _default_shards_path()
        self.runtime_root = Path(
            runtime_root or os.getenv("AAIS_RUNTIME_DIR") or Path(__file__).resolve().parents[3] / ".runtime"
        )
        self.tenants = tenants or TenantRegistry()
        self._payload = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"shards": {}}

    @property
    def shards(self) -> dict[str, GraphShardSpec]:
        parsed: dict[str, GraphShardSpec] = {}
        for shard_id, spec in dict(self._payload.get("shards") or {}).items():
            parsed[str(shard_id)] = GraphShardSpec(
                shard_id=str(shard_id),
                domain=str(spec.get("domain") or "global"),
                storage_backend=str(spec.get("storage_backend") or "jsonl"),
                enabled=bool(spec.get("enabled", True)),
            )
        return parsed

    def shard_root(self, shard_id: str) -> Path:
        return self.runtime_root / "collective-pattern-ledger" / "shards" / shard_id

    def resolve_shard_id(self, tenant_scope: str, *, domain: str | None = None) -> str:
        normalized = normalize_tenant_id(tenant_scope)
        tenant = self.tenants.get(normalized)
        if tenant and tenant.shard_id:
            return tenant.shard_id
        domain_key = str(domain or "global").strip().lower()
        for shard_id, spec in self.shards.items():
            if spec.domain == domain_key and spec.enabled:
                return shard_id
        return "shard-global"

    def list_shards(self) -> list[GraphShardSpec]:
        return [spec for spec in self.shards.values() if spec.enabled]
