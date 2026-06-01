"""Billing cycle enforcement (v8)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.billing.aggregator import export_usage_csv
from platform.store import PlatformStore


def default_org_billing_fields(*, owner_principal_id: str = "") -> dict[str, Any]:
    return {
        "oidc_provider": "local",
        "oidc_config": {},
        "billing_status": "active",
        "billing_cycle_start": datetime.now(UTC).date().isoformat(),
        "billing_owner_principal_id": owner_principal_id,
    }


def evaluate_billing_gate(org: dict[str, Any] | None) -> tuple[bool, str]:
    if not org:
        return True, "ok"
    status = str(org.get("billing_status") or "active")
    if status == "active":
        return True, "ok"
    if status == "past_due":
        return True, "ok"
    if status == "suspended":
        return False, "billing suspended"
    return False, f"billing status {status}"


def current_billing_period(org: dict[str, Any]) -> str:
    start = str(org.get("billing_cycle_start") or datetime.now(UTC).date().isoformat())
    return start[:7]


def close_billing_period(*, store: PlatformStore, org_id: str, period: str | None = None) -> dict[str, Any]:
    org = store.get_org(org_id) or {}
    period_key = period or current_billing_period(org)
    usage = store.list_usage(org_id=org_id, day_from=f"{period_key}-01", day_to=f"{period_key}-31")
    totals = {
        "org_id": org_id,
        "period": period_key,
        "jobs_count": sum(int(u.get("jobs_count") or 0) for u in usage),
        "mechanic_jobs": sum(int(u.get("mechanic_jobs") or 0) for u in usage),
        "slingshot_jobs": sum(int(u.get("slingshot_jobs") or 0) for u in usage),
        "estimated_cost": sum(float(u.get("estimated_cost") or 0) for u in usage),
        "status": "closed",
        "closed_at": datetime.now(UTC).isoformat(),
    }
    store.upsert_billing_period(totals)
    return totals


def billing_period_csv(*, store: PlatformStore, org_id: str, period: str) -> str:
    return export_usage_csv(store=store, org_id=org_id, month=period)
