"""Platform Membrane v41–v50 API routes (Sixth arc)."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from platform.events.dispatch import emit_org_event
from platform.exchange.envelope import build_envelope
from platform.exchange.intra_tenant import transfer_listing
from platform.exchange.peer import apply_inbound, push_outbound, upsert_peer
from platform.ledger.hooks import ledger_autopilot, ledger_exchange
from platform.ledger.ugr_bridge import query_cognition_overlay
from platform.ledger.writer import query_ledger, verify_ledger_chain
from platform.mesh.autopilot import get_routing_policy, run_autopilot, set_routing_policy
from platform.proof.federation import register_attestation
from platform.proof.witnesses import build_proof_graph, enroll_witness, list_witnesses
from platform.sovereign.export_pack import build_export_pack
from platform.sovereign.profile import get_sovereign_profile, set_sovereign_profile


class RoutingPolicyRequest(BaseModel):
    auto_assign_from_queue: bool = False
    suggest_on_call_on_drift: bool = False
    max_auto_assignments_per_run: int = 5


class WitnessEnrollRequest(BaseModel):
    witness_id: str
    region: str = "us"
    public_key_ref: str = ""


class WitnessAttestationRequest(BaseModel):
    job_id: str
    witness_id: str
    result_hash: str
    signature: str = ""


class ListingTransferRequest(BaseModel):
    source_org_id: str
    target_org_id: str
    consent_by: str = ""


class ExchangeOutboundRequest(BaseModel):
    peer_id: str
    tenant_id: str
    source_org_id: str
    target_org_id: str
    kind: str = "handoff.metadata"
    body: dict[str, Any] = Field(default_factory=dict)
    dual_consent: bool = True


class PeerUpsertRequest(BaseModel):
    peer_id: str
    base_url: str
    public_key: str = ""


class SovereignProfileRequest(BaseModel):
    mode: str = "hosted"
    data_residency: str = "us"
    export_bundle_schedule: str = ""
    runner_endpoint: str = ""


def register_v4150_routes(
    app: Any,
    *,
    svc: Any,
    cfg: Any,
    require_action: Any,
    require_org_action: Any,
) -> None:

    @app.put("/v1/orgs/{org_id}/mesh/routing-policy")
    def put_routing_policy(
        org_id: str,
        body: RoutingPolicyRequest,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        policy = set_routing_policy(store=svc.store, org_id=org_id, policy=body.model_dump())
        return {"routing_policy": policy}

    @app.get("/v1/orgs/{org_id}/mesh/routing-policy")
    def get_mesh_routing_policy(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id)
        return {"routing_policy": get_routing_policy(org)}

    @app.post("/v1/orgs/{org_id}/mesh/autopilot/run")
    def mesh_autopilot_run(
        org_id: str,
        mode: Literal["dry_run", "apply"] = "dry_run",
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        receipt = run_autopilot(
            store=svc.store,
            org_id=org_id,
            mode=mode,
            actor_principal_id=principal.principal_id,
        )
        ledger_autopilot(store=svc.store, receipt=receipt)
        if mode == "apply":
            emit_org_event(
                store=svc.store,
                org_id=org_id,
                event_type="mesh.autopilot",
                payload={"run_id": receipt.get("run_id"), "mode": mode},
            )
        return receipt

    @app.post("/v1/proof/witnesses/enroll")
    def proof_witness_enroll(
        body: WitnessEnrollRequest,
        principal: Any = Depends(require_action("org.admin")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        return enroll_witness(
            store=svc.store,
            witness_id=body.witness_id,
            region=body.region,
            public_key_ref=body.public_key_ref,
        )

    @app.get("/v1/proof/witnesses")
    def proof_witness_list(
        principal: Any = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        return {"witnesses": list_witnesses(store=svc.store)}

    @app.get("/v1/proof/network/graph")
    def proof_network_graph(
        job_id: str,
        principal: Any = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        job = svc.store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        if job.get("org_id") != principal.org_id and not principal.is_platform_admin():
            raise HTTPException(status_code=404, detail="job not found")
        return build_proof_graph(store=svc.store, job_id=job_id)

    @app.post("/v1/proof/witnesses/attest")
    def proof_witness_attest(
        body: WitnessAttestationRequest,
        principal: Any = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        if not principal.has_scope("proof:attest") and not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="proof:attest required")
        job = svc.store.get_job(body.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        try:
            from platform.ledger.hooks import ledger_attestation
            from platform.proof.quorum import evaluate_quorum

            att = register_attestation(
                store=svc.store,
                job_id=body.job_id,
                runner_id="",
                result_hash=body.result_hash,
                witness_id=body.witness_id,
                signature=body.signature,
            )
            ledger_attestation(store=svc.store, org_id=str(job.get("org_id") or ""), attestation=att)
            evaluate_quorum(
                store=svc.store,
                job=svc.store.get_job(body.job_id) or job,
                enqueue=lambda jid, region="us": svc.queue.enqueue(jid, region=region),
            )
            return att
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/v1/tenants/{tenant_id}/exchange/listings/{listing_id}/transfer")
    def exchange_listing_transfer(
        tenant_id: str,
        listing_id: str,
        body: ListingTransferRequest,
        principal: Any = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        try:
            result = transfer_listing(
                store=svc.store,
                tenant_id=tenant_id,
                listing_id=listing_id,
                source_org_id=body.source_org_id,
                target_org_id=body.target_org_id,
                consent_by=body.consent_by or principal.principal_id,
            )
            ledger_exchange(
                store=svc.store,
                org_id=body.source_org_id,
                kind="exchange.listing.transfer",
                payload={"listing_id": listing_id, "target_org_id": body.target_org_id},
            )
            return result
        except (PermissionError, ValueError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/v1/exchange/peers")
    def exchange_list_peers(
        principal: Any = Depends(require_action("org.admin")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        return {"peers": svc.store.list_platform_peers()}

    @app.post("/v1/exchange/peers")
    def exchange_upsert_peer(
        body: PeerUpsertRequest,
        principal: Any = Depends(require_action("org.admin")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        return upsert_peer(
            store=svc.store,
            peer_id=body.peer_id,
            base_url=body.base_url,
            public_key=body.public_key,
        )

    @app.post("/v1/exchange/outbound")
    def exchange_outbound(
        body: ExchangeOutboundRequest,
        principal: Any = Depends(require_action("org.admin")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        envelope = build_envelope(
            tenant_id=body.tenant_id,
            source_org_id=body.source_org_id,
            target_org_id=body.target_org_id,
            kind=body.kind,
            body=body.body,
            consent_by=principal.principal_id,
            dual_consent=body.dual_consent,
        )
        return push_outbound(store=svc.store, envelope=envelope, peer_id=body.peer_id)

    @app.post("/v1/exchange/inbound")
    def exchange_inbound(
        envelope: dict[str, Any],
        principal: Any = Depends(require_action("org.admin")),
    ) -> dict[str, Any]:
        if not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="platform_admin required")
        try:
            result = apply_inbound(store=svc.store, envelope=envelope)
            ledger_exchange(
                store=svc.store,
                org_id=str(envelope.get("source_org_id") or "platform"),
                kind="exchange.inbound",
                payload={"kind": envelope.get("kind"), "consent_id": envelope.get("consent_id")},
            )
            return result
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/v1/orgs/{org_id}/ledger/query")
    def ledger_query(
        org_id: str,
        kind: str = "",
        from_day: str = "",
        to_day: str = "",
        cursor: str = "",
        limit: int = 50,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        return query_ledger(
            store=svc.store,
            org_id=org_id,
            kind=kind,
            day_from=from_day,
            day_to=to_day,
            cursor=cursor,
            limit=limit,
        )

    @app.get("/v1/orgs/{org_id}/ledger/cognition-overlay")
    def ledger_cognition_overlay(
        org_id: str,
        limit: int = 50,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        return query_cognition_overlay(store=svc.store, org_id=org_id, limit=limit)

    @app.get("/v1/orgs/{org_id}/ledger/verify")
    def ledger_verify(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        ok, detail = verify_ledger_chain(store=svc.store, org_id=org_id)
        return {"valid": ok, "detail": detail, "claim_label": "asserted" if ok else "rejected"}

    @app.get("/v1/orgs/{org_id}/sovereign/profile")
    def sovereign_profile_get(
        org_id: str,
        principal: Any = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id)
        return {"sovereign_profile": get_sovereign_profile(org)}

    @app.put("/v1/orgs/{org_id}/sovereign/profile")
    def sovereign_profile_put(
        org_id: str,
        body: SovereignProfileRequest,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        profile = set_sovereign_profile(store=svc.store, org_id=org_id, profile=body.model_dump())
        return {"sovereign_profile": profile}

    @app.post("/v1/orgs/{org_id}/sovereign/export-pack")
    def sovereign_export_pack(
        org_id: str,
        principal: Any = Depends(require_org_action("org.admin")),
    ) -> Response:
        data, manifest = build_export_pack(store=svc.store, org_id=org_id)
        return Response(
            content=data,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{org_id}-sovereign-pack.zip"',
                "X-Platform-Manifest-Signature": str(manifest.get("signature") or ""),
            },
        )
