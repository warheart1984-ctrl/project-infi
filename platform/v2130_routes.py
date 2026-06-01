"""Platform Membrane v21–v30 API routes."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from platform.marketplace.analytics import marketplace_analytics
from platform.marketplace.lifecycle import approve_listing, deprecate_listing
from platform.mesh.policy import set_mesh_policy
from platform.mesh.stream import mesh_event_stream
from platform.proof.runners import enroll_runner
from platform.sovereign.exports import export_attestations_csv, export_audit_csv
from platform.sovereign.tenant import tenant_summary


class MeshPolicyRequest(BaseModel):
    max_assignments_per_operator: int = 0
    require_on_call_for_drift_investigation: bool = False


def register_v2130_routes(
    app: Any,
    *,
    svc: Any,
    cfg: Any,
    require_action: Any,
    require_org_action: Any,
) -> None:

    @app.get("/v1/orgs/{org_id}/mesh/events/stream")
    async def mesh_events_stream_route(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> StreamingResponse:
        async def gen() -> Any:
            async for chunk in mesh_event_stream(store=svc.store, org_id=org_id):
                yield chunk

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.put("/v1/orgs/{org_id}/mesh/policy")
    def put_mesh_policy(
        org_id: str,
        body: MeshPolicyRequest,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        return set_mesh_policy(
            store=svc.store,
            org_id=org_id,
            policy=body.model_dump(),
        )

    @app.get("/v1/orgs/{org_id}/mesh/policy")
    def get_mesh_policy(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id) or {}
        return {"mesh_policy": org.get("mesh_policy") or {}}

    @app.post("/v1/marketplace/listings/{listing_id}/approve")
    def approve_listing_route(
        listing_id: str,
        principal: Any = Depends(require_action("job.create")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        return approve_listing(
            store=svc.store,
            listing=listing,
            approved_by=principal.principal_id,
        )

    @app.post("/v1/marketplace/listings/{listing_id}/deprecate")
    def deprecate_listing_route(
        listing_id: str,
        org_id: str,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        return deprecate_listing(store=svc.store, listing=listing)

    @app.get("/v1/orgs/{org_id}/marketplace/analytics")
    def marketplace_analytics_route(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        return marketplace_analytics(store=svc.store, org_id=org_id)

    @app.post("/v1/proof/runners/enroll")
    def enroll_runner_route(
        body: dict[str, Any],
        principal: Any = Depends(require_action("job.create")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        return enroll_runner(
            store=svc.store,
            runner_id=str(body.get("runner_id") or ""),
            region=str(body.get("region") or "us"),
            public_key_ref=str(body.get("public_key_ref") or ""),
            public_key_pem=str(body.get("public_key_pem") or ""),
        )

    @app.get("/v1/proof/runners")
    def list_runners_route(
        principal: Any = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        return {"runners": svc.store.list_proof_runners()}

    @app.get("/v1/orgs/{org_id}/exports/audit")
    def export_audit(
        org_id: str,
        format: str = "csv",
        principal: Any = Depends(require_org_action("audit.read")),
    ) -> PlainTextResponse:
        if format != "csv":
            raise HTTPException(status_code=400, detail="only csv supported")
        return PlainTextResponse(export_audit_csv(store=svc.store, org_id=org_id))

    @app.get("/v1/orgs/{org_id}/exports/attestations")
    def export_attestations(
        org_id: str,
        from_day: str = "",
        to_day: str = "",
        principal: Any = Depends(require_org_action("job.read")),
    ) -> PlainTextResponse:
        return PlainTextResponse(
            export_attestations_csv(
                store=svc.store,
                org_id=org_id,
                day_from=from_day,
                day_to=to_day,
            )
        )

    @app.get("/v1/tenants/{ugr_tenant_id}/summary")
    def tenant_summary_route(
        ugr_tenant_id: str,
        principal: Any = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        return tenant_summary(store=svc.store, ugr_tenant_id=ugr_tenant_id)
