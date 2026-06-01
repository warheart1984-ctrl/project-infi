"""Platform Membrane v31–v40 API routes."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from platform.events.dispatch import emit_org_event
from platform.events.subscriptions import create_subscription, list_subscriptions
from platform.marketplace.catalog import bump_listing_version, search_catalog
from platform.marketplace.reviews import add_review
from platform.mesh.policy import set_mesh_policy
from platform.mesh.queue import get_assignment_queue, set_assignment_queue
from platform.mesh.retention import compact_org_mesh_events
from platform.proof.bundles import build_attestation_bundle
from platform.proof.runners import enroll_runner
from platform.sovereign.exports import export_attestations_csv, export_usage_csv_range


class WebhookCreateRequest(BaseModel):
    url: str
    event_types: list[str] = Field(default_factory=lambda: ["job.status"])


class ReviewRequest(BaseModel):
    rating: int
    comment: str = ""


class VersionBumpRequest(BaseModel):
    semver: str
    breaking: bool = False


class MeshQueueRequest(BaseModel):
    principal_ids: list[str] = Field(default_factory=list)


class CompliancePolicyRequest(BaseModel):
    retention_days: int = 90
    export_allowed_kinds: list[str] = Field(default_factory=lambda: ["audit", "attestations", "usage"])


class RunnerEnrollV3Request(BaseModel):
    runner_id: str
    region: str = "us"
    public_key_ref: str = ""
    public_key_pem: str = ""


def register_v3140_routes(
    app: Any,
    *,
    svc: Any,
    cfg: Any,
    require_action: Any,
    require_org_action: Any,
) -> None:

    @app.post("/v1/orgs/{org_id}/webhooks")
    def create_webhook(
        org_id: str,
        body: WebhookCreateRequest,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        return create_subscription(
            store=svc.store,
            org_id=org_id,
            url=body.url,
            event_types=body.event_types,
        )

    @app.get("/v1/orgs/{org_id}/webhooks")
    def list_webhooks(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        return {"subscriptions": list_subscriptions(store=svc.store, org_id=org_id)}

    @app.delete("/v1/orgs/{org_id}/webhooks/{subscription_id}")
    def delete_webhook(
        org_id: str,
        subscription_id: str,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, str]:
        sub = svc.store.get_webhook_subscription(subscription_id)
        if not sub or sub.get("org_id") != org_id:
            raise HTTPException(status_code=404, detail="subscription not found")
        svc.store.delete_webhook_subscription(subscription_id)
        return {"status": "deleted"}

    @app.post("/v1/marketplace/listings/{listing_id}/reviews")
    def post_review(
        listing_id: str,
        org_id: str,
        body: ReviewRequest,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        return add_review(
            store=svc.store,
            listing_id=listing_id,
            org_id=org_id,
            principal_id=principal.principal_id,
            rating=body.rating,
            comment=body.comment,
        )

    @app.get("/v1/marketplace/catalog")
    def marketplace_catalog(
        org_id: str,
        q: str = "",
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id) or {}
        items = search_catalog(
            store=svc.store,
            org_id=org_id,
            ugr_tenant_id=str(org.get("ugr_tenant_id") or f"tenant:{org_id}"),
            is_platform_admin=principal.is_platform_admin(),
            query=q,
        )
        return {"listings": items}

    @app.patch("/v1/marketplace/listings/{listing_id}/version")
    def bump_version(
        listing_id: str,
        org_id: str,
        body: VersionBumpRequest,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        return bump_listing_version(
            store=svc.store,
            listing=listing,
            semver=body.semver,
            breaking=body.breaking,
        )

    @app.get("/v1/jobs/{job_id}/attestations/bundle")
    def attestation_bundle(
        job_id: str,
        principal: Any = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        try:
            return build_attestation_bundle(store=svc.store, job_id=job_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/v1/proof/runners/enroll/v3")
    def enroll_runner_v3(
        body: RunnerEnrollV3Request,
        principal: Any = Depends(require_action("job.create")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        return enroll_runner(
            store=svc.store,
            runner_id=body.runner_id,
            region=body.region,
            public_key_ref=body.public_key_ref,
            public_key_pem=body.public_key_pem,
        )

    @app.put("/v1/orgs/{org_id}/mesh/queue")
    def put_mesh_queue(
        org_id: str,
        body: MeshQueueRequest,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        ids = set_assignment_queue(store=svc.store, org_id=org_id, principal_ids=body.principal_ids)
        return {"assignment_queue": ids}

    @app.get("/v1/orgs/{org_id}/mesh/queue")
    def get_mesh_queue(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id) or {}
        return {"assignment_queue": get_assignment_queue(org)}

    @app.post("/v1/orgs/{org_id}/mesh/compact")
    def mesh_compact(
        org_id: str,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        removed = compact_org_mesh_events(store=svc.store, org_id=org_id)
        return {"removed": removed}

    @app.get("/v1/orgs/{org_id}/exports/usage")
    def export_usage(
        org_id: str,
        from_day: str = "",
        to_day: str = "",
        principal: Any = Depends(require_org_action("usage.read")),
    ) -> PlainTextResponse:
        return PlainTextResponse(
            export_usage_csv_range(store=svc.store, org_id=org_id, day_from=from_day, day_to=to_day)
        )

    @app.put("/v1/orgs/{org_id}/compliance/policy")
    def put_compliance_policy(
        org_id: str,
        body: CompliancePolicyRequest,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id) or {"org_id": org_id}
        org["compliance_policy"] = body.model_dump()
        svc.store.upsert_org(org)
        policy = dict(org.get("mesh_policy") or {})
        policy["event_retention_days"] = body.retention_days
        set_mesh_policy(store=svc.store, org_id=org_id, policy=policy)
        return org["compliance_policy"]

    @app.get("/v1/orgs/{org_id}/compliance/policy")
    def get_compliance_policy(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id) or {}
        return {"compliance_policy": org.get("compliance_policy") or {}}

    @app.post("/v1/orgs/{org_id}/events/emit-test")
    def emit_test_event(
        org_id: str,
        event_type: str = "job.status",
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        """Test-only hook to exercise webhook dispatch without Stage 3 actuation."""
        deliveries = emit_org_event(
            store=svc.store,
            org_id=org_id,
            event_type=event_type,
            payload={"test": True, "actor": principal.principal_id},
        )
        return {"deliveries": deliveries}
