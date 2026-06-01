"""Publish workflow listings."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from datetime import datetime

from src.datetime_compat import UTC

from platform.common import new_id
from platform.marketplace.lifecycle import default_approval_status
from platform.marketplace.visibility import can_publish_visibility
from platform.store import PlatformStore
from platform.workflow.compiler import compile_steps

LISTING_VERSION = "platform.workflow_listing.v1"


def publish_listing(
    *,
    store: PlatformStore,
    org_id: str,
    ugr_tenant_id: str,
    name: str,
    steps: list[dict[str, str]],
    visibility: str,
    semver: str = "1.0.0",
    curated: bool = False,
    proof_requirements: list[str] | None = None,
    workflow_id: str = "",
    is_platform_admin: bool = False,
) -> dict[str, Any]:
    ok, reason = can_publish_visibility(
        visibility=visibility,
        is_platform_admin=is_platform_admin,
        curated=curated,
    )
    if not ok:
        raise PermissionError(reason)
    plan = compile_steps(steps)
    source_hash = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()[:16]
    approval = default_approval_status(visibility=visibility, is_platform_admin=is_platform_admin)
    listing = {
        "listing_version": LISTING_VERSION,
        "listing_id": new_id("lst"),
        "workflow_id": workflow_id or new_id("wf"),
        "org_id": org_id,
        "ugr_tenant_id": ugr_tenant_id,
        "name": name,
        "visibility": visibility,
        "curated": curated,
        "semver": semver,
        "steps": steps,
        "plan": plan,
        "source_hash": source_hash,
        "proof_requirements": proof_requirements or [],
        "approval_status": approval,
        "published_at": datetime.now(UTC).isoformat() if approval == "published" else "",
        "claim_label": "asserted",
    }
    store.upsert_listing(listing)
    return listing
