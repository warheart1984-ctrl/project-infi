"""Install / fork listings into org workflows."""

from __future__ import annotations

from typing import Any, Callable

from platform.marketplace.lifecycle import listing_installable
from platform.marketplace.visibility import can_view_listing
from platform.store import PlatformStore
from platform.workflow.engine import start_workflow_run
from platform.workflow.schema import build_workflow


def install_listing(
    *,
    store: PlatformStore,
    listing: dict[str, Any],
    target_org_id: str,
    ugr_tenant_id: str,
    is_platform_admin: bool,
) -> dict[str, Any]:
    if not can_view_listing(
        listing=listing,
        org_id=target_org_id,
        ugr_tenant_id=ugr_tenant_id,
        is_platform_admin=is_platform_admin,
    ):
        raise PermissionError("listing not visible to org")
    ok, reason = listing_installable(listing)
    if not ok:
        raise PermissionError(reason)
    wf = build_workflow(
        org_id=target_org_id,
        name=f"{listing.get('name')}-installed",
        steps=list(listing.get("steps") or []),
    )
    wf["source_listing_id"] = listing["listing_id"]
    wf["installed_version"] = listing.get("semver")
    wf["proof_requirements"] = list(listing.get("proof_requirements") or [])
    store.upsert_workflow(wf)
    return wf


def fork_listing(
    *,
    store: PlatformStore,
    listing: dict[str, Any],
    target_org_id: str,
    ugr_tenant_id: str,
    is_platform_admin: bool,
) -> dict[str, Any]:
    wf = install_listing(
        store=store,
        listing=listing,
        target_org_id=target_org_id,
        ugr_tenant_id=ugr_tenant_id,
        is_platform_admin=is_platform_admin,
    )
    wf["forked_from"] = listing["listing_id"]
    store.upsert_workflow(wf)
    return wf


def run_installed_listing(
    *,
    store: PlatformStore,
    listing: dict[str, Any],
    target_org_id: str,
    actor_principal_id: str,
    enqueue: Callable[..., bool],
) -> dict[str, Any]:
    wf = store.list_workflows(org_id=target_org_id)
    match = next((w for w in wf if w.get("source_listing_id") == listing["listing_id"]), None)
    if not match:
        raise ValueError("listing not installed; install first")
    parent = start_workflow_run(
        store=store,
        org_id=target_org_id,
        workflow=match,
        actor_principal_id=actor_principal_id,
        enqueue=enqueue,
    )
    meta = dict(parent.get("metadata") or {})
    meta["source_listing_id"] = listing["listing_id"]
    meta["proof_requirements"] = list(listing.get("proof_requirements") or [])
    parent["metadata"] = meta
    store.upsert_job(parent)
    return parent
