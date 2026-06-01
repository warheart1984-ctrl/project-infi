"""Read-only Platform ↔ UGR cognition ledger overlay."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from platform.store import PlatformStore


def _tenant_scope_for_org(org: dict[str, Any] | None) -> str:
    if not org:
        return "global"
    raw = str(org.get("ugr_tenant_id") or "").strip()
    if not raw or raw == "global":
        return "global"
    if raw.startswith("tenant:"):
        return raw
    return f"tenant:{raw}"


def query_cognition_overlay(
    *,
    store: PlatformStore,
    org_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    org = store.get_org(org_id)
    tenant_scope = _tenant_scope_for_org(org)
    runtime_root = Path(os.environ.get("AAIS_RUNTIME_DIR", ".runtime/aais-data"))
    try:
        from src.ugr.platform.sharded_ledger import ShardedPatternLedger

        ledger = ShardedPatternLedger(runtime_root=str(runtime_root))
        claims = ledger.read_claims(tenant_scope=tenant_scope, limit=limit)
    except Exception as exc:
        return {
            "org_id": org_id,
            "tenant_scope": tenant_scope,
            "claims": [],
            "error": str(exc),
            "claim_label": "asserted",
            "read_only": True,
        }
    return {
        "org_id": org_id,
        "tenant_scope": tenant_scope,
        "claims": claims,
        "count": len(claims),
        "claim_label": "asserted",
        "read_only": True,
    }
