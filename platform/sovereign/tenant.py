"""Tenant summary API (v30)."""

from __future__ import annotations

from typing import Any

from platform.store import PlatformStore


def tenant_summary(*, store: PlatformStore, ugr_tenant_id: str) -> dict[str, Any]:
    orgs = store.list_orgs_by_tenant(ugr_tenant_id)
    total_jobs = 0
    drift_open = 0
    disputed = 0
    installs = 0
    webhook_failures = 0
    sovereign_modes: dict[str, int] = {"hosted": 0, "self_hosted": 0}
    for org in orgs:
        oid = str(org["org_id"])
        jobs = store.list_jobs(org_id=oid)
        total_jobs += len(jobs)
        webhook_failures += store.count_webhook_failures(org_id=oid)
        mode = str((org.get("sovereign_profile") or {}).get("mode") or "hosted")
        sovereign_modes[mode] = sovereign_modes.get(mode, 0) + 1
        for j in jobs:
            if j.get("subsystem") == "drift_detector" and j.get("status") not in {"complete", "cancelled"}:
                drift_open += 1
            if j.get("proof_status") == "disputed":
                disputed += 1
        for u in store.list_usage(org_id=oid):
            installs += int(u.get("marketplace_installs") or 0)
    return {
        "ugr_tenant_id": ugr_tenant_id,
        "org_count": len(orgs),
        "org_ids": [str(o["org_id"]) for o in orgs],
        "total_jobs": total_jobs,
        "drift_open": drift_open,
        "proof_disputed": disputed,
        "marketplace_installs": installs,
        "webhook_delivery_failures": webhook_failures,
        "sovereign_mode_breakdown": sovereign_modes,
    }
