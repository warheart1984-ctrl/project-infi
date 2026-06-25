"""Survivability dashboard API — Article S / S-2 integration payload for HUD and CLI."""

from __future__ import annotations

from typing import Any

from constitutional.runtime.runtime import ConstitutionalStateRuntime
from operator_kernel.succession_integration import (
    ArticleS2IntegrationSnapshot,
    build_article_s2_integration_snapshot,
)


def get_survivability_csr() -> ConstitutionalStateRuntime:
    """Resolve process CSR (operator kernel tasks dir, else URG persist root)."""
    try:
        from operator_kernel.csr import CSR

        return CSR
    except Exception:
        from src.ugr.state_runtime import CSR

        return CSR


def build_survivability_dashboard_payload(
    csr: ConstitutionalStateRuntime | None = None,
    *,
    refresh: bool = False,
    escalate_amendment: bool = True,
) -> dict[str, Any]:
    """JSON-serializable survivability cockpit for `/api/survivability/dashboard`."""
    runtime = csr or get_survivability_csr()
    snapshot = build_article_s2_integration_snapshot(
        runtime,
        refresh=refresh,
        escalate_amendment=escalate_amendment,
    )
    return snapshot_to_api_dict(snapshot)


def snapshot_to_api_dict(snapshot: ArticleS2IntegrationSnapshot) -> dict[str, Any]:
    return snapshot.model_dump(mode="json")
