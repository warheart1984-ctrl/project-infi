"""Platform Membrane v15–v20 API routes."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from platform.auth.audit import append_audit_event
from platform.auth.rbac import Principal, authorize_scope
from platform.billing.aggregator import record_marketplace_event
from platform.marketplace.catalog import list_visible_listings
from platform.marketplace.install import fork_listing, install_listing, run_installed_listing
from platform.marketplace.publish import publish_listing
from platform.mesh.assignment import assign_job, release_assignment
from platform.mesh.handoff import create_handoff_bundle
from platform.mesh.on_call import current_on_call, set_on_call_schedule
from platform.mesh.presence import heartbeat_presence, list_online_operators
from platform.proof.federation import federation_status, register_attestation
from platform.proof.quorum import evaluate_quorum
from platform.service import PlatformService
from platform.settings import PlatformSettings
from platform.store import PlatformStore


class PresenceRequest(BaseModel):
    status: str = "online"
    session_id: str = ""


class AssignRequest(BaseModel):
    assignee_principal_id: str
    org_id: str = ""


class OnCallRequest(BaseModel):
    principal_ids: list[str] = Field(default_factory=list)
    effective_from: str = ""
    effective_to: str = ""


class HandoffRequest(BaseModel):
    to_principal_id: str
    notes: str = ""
    runbook_ref: str = ""


class ListingPublishRequest(BaseModel):
    org_id: str
    name: str
    steps: list[dict[str, str]] = Field(default_factory=list)
    visibility: str = "org"
    semver: str = "1.0.0"
    curated: bool = False
    proof_requirements: list[str] = Field(default_factory=list)


class ListingPatchRequest(BaseModel):
    semver: str


class AttestationRequest(BaseModel):
    runner_id: str
    result_hash: str
    region: str = "us"
    machine_label: str = ""
    manifest_ref: str = ""
    signature: str = ""


def register_v1520_routes(
    app: Any,
    *,
    svc: PlatformService,
    cfg: PlatformSettings,
    require_action: Any,
    require_org_action: Any,
) -> None:

    @app.post("/v1/orgs/{org_id}/mesh/presence")
    def mesh_presence(
        org_id: str,
        body: PresenceRequest,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        rec = heartbeat_presence(
            store=svc.store,
            org_id=org_id,
            principal_id=principal.principal_id,
            status=body.status,
            session_id=body.session_id,
        )
        return rec

    @app.get("/v1/orgs/{org_id}/mesh/operators")
    def mesh_operators(
        org_id: str,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        return {"operators": list_online_operators(store=svc.store, org_id=org_id)}

    @app.get("/v1/orgs/{org_id}/mesh/events")
    def mesh_events(
        org_id: str,
        limit: int = 50,
        cursor: str = "",
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        if cursor:
            events = svc.store.list_mesh_events_after(org_id=org_id, cursor=cursor, limit=limit)
        else:
            events = svc.store.list_mesh_events(org_id=org_id, limit=limit)
        return {"events": events, "cursor": cursor}

    @app.post("/v1/jobs/{job_id}/assign")
    def job_assign(
        job_id: str,
        org_id: str,
        body: AssignRequest,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, Any]:
        target_org = body.org_id or org_id
        try:
            rec = assign_job(
                store=svc.store,
                job_id=job_id,
                org_id=target_org,
                assignee_principal_id=body.assignee_principal_id,
                assigned_by=principal.principal_id,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if cfg.audit_path:
            append_audit_event(
                audit_path=cfg.audit_path,
                org_id=target_org,
                principal_id=principal.principal_id,
                action="mesh.assign",
                job_id=job_id,
                store=svc.store,
            )
        return rec

    @app.delete("/v1/jobs/{job_id}/assign")
    def job_unassign(
        job_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, str]:
        release_assignment(
            store=svc.store,
            job_id=job_id,
            org_id=org_id,
            actor_principal_id=principal.principal_id,
        )
        return {"status": "released"}

    @app.get("/v1/mesh/external-health")
    def external_mesh_health() -> dict[str, Any]:
        urls = os.environ.get("PLATFORM_MESH_HEALTH_URLS", "").split(",")
        services = []
        for raw in urls:
            url = raw.strip()
            if not url:
                continue
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    body = json.loads(resp.read().decode())
                services.append({"url": url, "status": "ok", "health": body})
            except Exception as exc:
                services.append({"url": url, "status": "unreachable", "error": str(exc)})
        return {"services": services, "runtime_effect": "readout_only"}

    @app.put("/v1/orgs/{org_id}/on-call")
    def put_on_call(
        org_id: str,
        body: OnCallRequest,
        principal: Principal = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        return set_on_call_schedule(
            store=svc.store,
            org_id=org_id,
            principal_ids=body.principal_ids,
            effective_from=body.effective_from,
            effective_to=body.effective_to,
        )

    @app.get("/v1/orgs/{org_id}/on-call/current")
    def get_on_call(
        org_id: str,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        pid = current_on_call(store=svc.store, org_id=org_id)
        return {"principal_id": pid}

    @app.post("/v1/orgs/{org_id}/mesh/handoff")
    def mesh_handoff(
        org_id: str,
        body: HandoffRequest,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, Any]:
        return create_handoff_bundle(
            store=svc.store,
            org_id=org_id,
            from_principal_id=principal.principal_id,
            to_principal_id=body.to_principal_id,
            notes=body.notes,
            runbook_ref=body.runbook_ref,
        )

    @app.get("/v1/orgs/{org_id}/mesh/handoff/{bundle_id}")
    def get_handoff(
        org_id: str,
        bundle_id: str,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        bundle = svc.store.get_handoff(bundle_id)
        if not bundle or bundle.get("org_id") != org_id:
            raise HTTPException(status_code=404, detail="handoff not found")
        return bundle

    @app.post("/v1/orgs/{org_id}/marketplace/listings")
    def marketplace_publish(
        org_id: str,
        body: ListingPublishRequest,
        principal: Principal = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="org not found")
        try:
            listing = publish_listing(
                store=svc.store,
                org_id=org_id,
                ugr_tenant_id=str(org.get("ugr_tenant_id") or f"tenant:{org_id}"),
                name=body.name,
                steps=body.steps,
                visibility=body.visibility,
                semver=body.semver,
                curated=body.curated,
                proof_requirements=body.proof_requirements,
                is_platform_admin=principal.is_platform_admin(),
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return listing

    @app.get("/v1/marketplace/listings")
    def marketplace_list(
        org_id: str,
        visibility: str = "",
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id) or {}
        items = list_visible_listings(
            store=svc.store,
            org_id=org_id,
            ugr_tenant_id=str(org.get("ugr_tenant_id") or f"tenant:{org_id}"),
            is_platform_admin=principal.is_platform_admin(),
            visibility_filter=visibility,
        )
        return {"listings": items}

    @app.get("/v1/marketplace/listings/{listing_id}")
    def marketplace_get(
        listing_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        org = svc.store.get_org(org_id) or {}
        from platform.marketplace.visibility import can_view_listing

        if not can_view_listing(
            listing=listing,
            org_id=org_id,
            ugr_tenant_id=str(org.get("ugr_tenant_id") or ""),
            is_platform_admin=principal.is_platform_admin(),
        ):
            raise HTTPException(status_code=404, detail="listing not found")
        return listing

    @app.patch("/v1/marketplace/listings/{listing_id}")
    def marketplace_patch(
        listing_id: str,
        body: ListingPatchRequest,
        principal: Principal = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        listing["semver"] = body.semver
        svc.store.upsert_listing(listing)
        return listing

    @app.post("/v1/marketplace/listings/{listing_id}/install")
    def marketplace_install(
        listing_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        org = svc.store.get_org(org_id) or {}
        try:
            wf = install_listing(
                store=svc.store,
                listing=listing,
                target_org_id=org_id,
                ugr_tenant_id=str(org.get("ugr_tenant_id") or ""),
                is_platform_admin=principal.is_platform_admin(),
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        record_marketplace_event(
            store=svc.store,
            org_id=org_id,
            event_type="install",
            listing_id=listing_id,
        )
        return wf

    @app.post("/v1/marketplace/listings/{listing_id}/fork")
    def marketplace_fork(
        listing_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        org = svc.store.get_org(org_id) or {}
        try:
            return fork_listing(
                store=svc.store,
                listing=listing,
                target_org_id=org_id,
                ugr_tenant_id=str(org.get("ugr_tenant_id") or ""),
                is_platform_admin=principal.is_platform_admin(),
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/v1/marketplace/listings/{listing_id}/run")
    def marketplace_run(
        listing_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, Any]:
        listing = svc.store.get_listing(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="listing not found")
        try:
            job = run_installed_listing(
                store=svc.store,
                listing=listing,
                target_org_id=org_id,
                actor_principal_id=principal.principal_id,
                enqueue=lambda jid, region="us": svc.queue.enqueue(jid, region=region),
            )
        except (PermissionError, ValueError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        record_marketplace_event(store=svc.store, org_id=org_id, event_type="workflow_run")
        return {"workflow_run": job}

    @app.post("/v1/jobs/{job_id}/attestations")
    def submit_attestation(
        job_id: str,
        body: AttestationRequest,
        principal: Principal = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        if not principal.has_scope("proof:attest") and not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="proof:attest required")
        job = svc.store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        try:
            att = register_attestation(
                store=svc.store,
                job_id=job_id,
                runner_id=body.runner_id,
                result_hash=body.result_hash,
                region=body.region,
                machine_label=body.machine_label,
                manifest_ref=body.manifest_ref,
                signature=body.signature,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        fresh = svc.store.get_job(job_id) or job
        evaluate_quorum(
            store=svc.store,
            job=fresh,
            enqueue=lambda jid, region="us": svc.queue.enqueue(jid, region=region),
        )
        return att

    @app.get("/v1/jobs/{job_id}/attestations")
    def list_attestations(
        job_id: str,
        principal: Principal = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        job = svc.store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return {"attestations": svc.store.list_attestations(job_id=job_id)}

    @app.get("/v1/proof/federation/{federation_id}")
    def get_federation(
        federation_id: str,
        principal: Principal = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        job = svc.store.get_job(federation_id)
        if not job:
            for org in svc.store.list_orgs():
                for j in svc.store.list_jobs(org_id=str(org["org_id"])):
                    if str(j.get("federation_id")) == federation_id:
                        job = j
                        break
        if not job:
            raise HTTPException(status_code=404, detail="federation not found")
        return federation_status(store=svc.store, job=job)
