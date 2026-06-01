"""Sharded pattern ledger with tenant overlay queries."""

from __future__ import annotations

from hashlib import sha256
import threading
from pathlib import Path
from typing import Any

from src.ugr.platform.graph_shard import GraphShardRouter
from src.ugr.platform.tenant_registry import TenantRegistry, normalize_tenant_id
from src.ugr.unified_pattern_ledger import UnifiedPatternLedger, _stable_json


class ShardedPatternLedger:
    """Phase 4 ledger — shard routing + global/tenant overlay reads."""

    def __init__(
        self,
        *,
        runtime_root: str | None = None,
        router: GraphShardRouter | None = None,
        tenants: TenantRegistry | None = None,
    ):
        self.router = router or GraphShardRouter(runtime_root=runtime_root)
        self.tenants = tenants or TenantRegistry()
        self._lock = threading.Lock()
        self._ledgers: dict[str, UnifiedPatternLedger] = {}

    def _ledger_for_shard(self, shard_id: str) -> UnifiedPatternLedger:
        with self._lock:
            if shard_id not in self._ledgers:
                self._ledgers[shard_id] = UnifiedPatternLedger(runtime_root=self.router.shard_root(shard_id))
            return self._ledgers[shard_id]

    def append_claim(self, claim: dict[str, Any], *, origin: str = "ugr") -> dict[str, Any]:
        tenant_scope = normalize_tenant_id(claim.get("tenant_scope") or "global")
        tenant = self.tenants.get(tenant_scope)
        if tenant and not tenant.enabled:
            raise ValueError(f"tenant disabled: {tenant_scope}")
        shard_id = self.router.resolve_shard_id(tenant_scope)
        payload = dict(claim)
        payload["tenant_scope"] = tenant_scope
        payload["shard_id"] = shard_id
        record = self._ledger_for_shard(shard_id).append_claim(payload, origin=origin)
        record["shard_id"] = shard_id
        return record

    def append_evidence(self, **kwargs: Any) -> dict[str, Any]:
        tenant_scope = normalize_tenant_id(kwargs.get("tenant_scope") or "global")
        shard_id = self.router.resolve_shard_id(tenant_scope)
        record = self._ledger_for_shard(shard_id).append_evidence(**kwargs)
        record["shard_id"] = shard_id
        return record

    def append_pattern_event(self, entry: dict[str, Any], *, mirror_legacy: bool = True) -> dict[str, Any]:
        tenant_scope = normalize_tenant_id(entry.get("tenant_scope") or "global")
        shard_id = self.router.resolve_shard_id(tenant_scope)
        record = self._ledger_for_shard(shard_id).append_pattern_event(entry, mirror_legacy=mirror_legacy)
        record["shard_id"] = shard_id
        return record

    def read_claims(self, *, tenant_scope: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        normalized = normalize_tenant_id(tenant_scope or "global")
        tenant = self.tenants.get(normalized)
        if tenant and not tenant.enabled:
            return []
        rows: list[dict[str, Any]] = []
        if tenant and tenant.overlay_global and normalized != "global":
            global_shard = self.router.resolve_shard_id("global")
            rows.extend(self._ledger_for_shard(global_shard).read_claims(tenant_scope="global", limit=limit))
        shard_id = self.router.resolve_shard_id(normalized)
        rows.extend(
            self._ledger_for_shard(shard_id).read_claims(
                tenant_scope=None if normalized == "global" else normalized,
                limit=limit,
            )
        )
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in rows:
            key = str(row.get("claim_id") or row.get("timestamp"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        max_rows = tenant.max_claims_per_query if tenant else limit
        return deduped[-max_rows:]

    def query_related(self, terms: list[str], *, tenant_scope: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        claims = self.read_claims(tenant_scope=tenant_scope, limit=max(limit * 4, 80))
        normalized_terms = [" ".join(str(term).split()).strip().lower() for term in terms if str(term).strip()]
        if not normalized_terms:
            return []
        query_tenant = normalize_tenant_id(tenant_scope or "global")
        matches: list[dict[str, Any]] = []
        for row in claims:
            row_tenant = normalize_tenant_id(row.get("tenant_scope") or "global")
            if query_tenant != "global" and row_tenant not in {query_tenant, "global"}:
                continue
            haystack = " ".join(
                [str(row.get("subject") or ""), str(row.get("predicate") or ""), str(row.get("object") or "")]
            ).lower()
            if any(term in haystack for term in normalized_terms):
                matches.append(row)
        return matches[-limit:]

    def configure_runtime_root(self, runtime_root: str | Path) -> None:
        self.router.runtime_root = Path(runtime_root)
        with self._lock:
            self._ledgers.clear()

    def make_claim_id(self, subject: str, predicate: str, object_value: str, source_lane: str) -> str:
        digest = sha256(
            _stable_json(
                {
                    "subject": subject,
                    "predicate": predicate,
                    "object": object_value,
                    "source_lane": source_lane,
                }
            ).encode("utf-8")
        ).hexdigest()[:16]
        return f"claim-{digest}"
