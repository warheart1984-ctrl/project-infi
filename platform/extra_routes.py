"""Additional v1.1–v7 platform API routes."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from platform.auth.audit import append_audit_event
from platform.auth.oidc import issue_session_token
from platform.auth.rbac import Principal, authorize_scope
from platform.billing.aggregator import export_usage_csv, record_job_completion
from platform.jobs.graph import build_job_graph
from platform.policy.engine import evaluate_admission
from platform.proof.runner import promote_consensus, run_proof_for_job
from platform.service import PlatformService
from platform.settings import PlatformSettings
from platform.v814_routes import patch_oidc_routes, register_v814_routes
from platform.v1520_routes import register_v1520_routes
from platform.v2130_routes import register_v2130_routes
from platform.v3140_routes import register_v3140_routes
from platform.v4150_routes import register_v4150_routes
from src.datetime_compat import UTC


class CreateInviteRequest(BaseModel):
    email: str
    role: str = "operator"


class AcceptInviteRequest(BaseModel):
    token: str
    principal_id: str
    display_name: str = ""


class SetRolesRequest(BaseModel):
    roles: list[str]


class CreateApiKeyScopedRequest(BaseModel):
    principal_id: str
    roles: list[str] = Field(default_factory=lambda: ["operator"])
    scopes: list[str] = Field(default_factory=list)
    display_name: str = ""
    principal_kind: str = "service_account"


def register_extra_routes(
    app: Any,
    *,
    svc: PlatformService,
    cfg: PlatformSettings,
    resolve_principal: Any,
    require_action: Any,
    require_org_action: Any,
) -> None:

    @app.get("/v1/orgs")
    def list_orgs(principal: Principal = Depends(require_action("org.read"))) -> dict[str, Any]:
        if principal.is_platform_admin():
            return {"orgs": svc.store.list_orgs()}
        org = svc.store.get_org(principal.org_id)
        return {"orgs": [org] if org else []}

    @app.get("/v1/orgs/{org_id}/principals")
    def list_principals(
        org_id: str,
        principal: Principal = Depends(require_org_action("principal.manage")),
    ) -> dict[str, Any]:
        return {"principals": svc.store.list_principals(org_id=org_id)}

    @app.put("/v1/orgs/{org_id}/principals/{principal_id}/roles")
    def set_principal_roles(
        org_id: str,
        principal_id: str,
        body: SetRolesRequest,
        actor: Principal = Depends(require_org_action("principal.manage")),
    ) -> dict[str, Any]:
        bindings = []
        for role in body.roles:
            bindings.append(
                svc.store.upsert_role_binding(
                    org_id=org_id,
                    principal_id=principal_id,
                    role=role,
                    granted_by=actor.principal_id,
                )
            )
        if cfg.audit_path:
            append_audit_event(
                audit_path=cfg.audit_path,
                org_id=org_id,
                principal_id=actor.principal_id,
                action="role.change",
                details={"target": principal_id, "roles": body.roles},
                store=svc.store,
            )
        return {"bindings": bindings}

    @app.post("/v1/orgs/{org_id}/api-keys/v2")
    def create_api_key_scoped(
        org_id: str,
        body: CreateApiKeyScopedRequest,
        principal: Principal = Depends(require_org_action("api_key.create")),
    ) -> dict[str, Any]:
        svc.store.upsert_principal(
            {
                "principal_id": body.principal_id,
                "org_id": org_id,
                "roles": body.roles,
                "principal_kind": body.principal_kind,
                "display_name": body.display_name,
            }
        )
        for role in body.roles:
            svc.store.upsert_role_binding(
                org_id=org_id,
                principal_id=body.principal_id,
                role=role,
                granted_by=principal.principal_id,
            )
        raw, api_key_id, rec = svc.store.create_api_key(
            org_id=org_id,
            principal_id=body.principal_id,
            roles=body.roles,
            scopes=body.scopes,
            display_name=body.display_name,
        )
        return {"api_key": raw, "api_key_id": api_key_id, "scopes": rec.get("scopes"), "org_id": org_id}

    @app.post("/v1/orgs/{org_id}/invites")
    def create_invite(
        org_id: str,
        body: CreateInviteRequest,
        principal: Principal = Depends(require_org_action("invite.create")),
    ) -> dict[str, Any]:
        token = secrets.token_urlsafe(24)
        expires = (datetime.now(UTC) + timedelta(days=7)).isoformat()
        invite = svc.store.create_invite(
            org_id=org_id,
            email=body.email,
            role=body.role,
            token=token,
            expires_at=expires,
            created_by=principal.principal_id,
        )
        base = os.environ.get("PLATFORM_INVITE_BASE_URL", "http://127.0.0.1:3000/platform/getting-started")
        invite["accept_url"] = f"{base}?token={token}&org_id={org_id}"
        return invite

    @app.post("/v1/invites/accept")
    def accept_invite(body: AcceptInviteRequest) -> dict[str, Any]:
        result = svc.store.accept_invite(
            token=body.token,
            principal_id=body.principal_id,
            display_name=body.display_name,
        )
        if not result:
            raise HTTPException(status_code=400, detail="invalid or expired invite")
        return result

    @app.get("/v1/jobs/{job_id}/graph")
    def job_graph(
        job_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        return build_job_graph(store=svc.store, job_id=job_id, org_id=org_id)

    @app.post("/v1/jobs/{job_id}/proof")
    def job_proof(
        job_id: str,
        machine: str = "primary",
        principal: Principal = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        job = svc.store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        if job.get("org_id") != principal.org_id and not principal.is_platform_admin():
            raise HTTPException(status_code=404, detail="job not found")
        report = run_proof_for_job(job=job, machine_label=machine)
        h = str(report.get("result_hash") or "")
        if machine == "primary":
            job = promote_consensus(job=job, primary_hash=h, secondary_hash=str(job.get("secondary_hash") or ""))
        else:
            job = promote_consensus(job=job, primary_hash=str(job.get("primary_hash") or ""), secondary_hash=h)
        svc.store.upsert_job(job)
        return {"job": job, "report": report}

    @app.get("/v1/orgs/{org_id}/usage")
    def org_usage(
        org_id: str,
        from_day: str = "",
        to_day: str = "",
        format: Literal["json", "csv"] = "json",
        principal: Principal = Depends(require_org_action("usage.read")),
    ) -> Any:
        if not authorize_scope(principal=principal, scope="org:billing", target_org_id=org_id):
            raise HTTPException(status_code=403, detail="forbidden")
        rows = svc.store.list_usage(org_id=org_id, day_from=from_day, day_to=to_day)
        if format == "csv":
            from fastapi.responses import PlainTextResponse

            month = (from_day or datetime.now(UTC).date().isoformat())[:7]
            return PlainTextResponse(export_usage_csv(store=svc.store, org_id=org_id, month=month))
        return {"usage": rows}

    register_v814_routes(
        app,
        svc=svc,
        cfg=cfg,
        resolve_principal=resolve_principal,
        require_action=require_action,
        require_org_action=require_org_action,
    )
    patch_oidc_routes(app, svc=svc, cfg=cfg)
    register_v1520_routes(
        app,
        svc=svc,
        cfg=cfg,
        require_action=require_action,
        require_org_action=require_org_action,
    )
    register_v2130_routes(
        app,
        svc=svc,
        cfg=cfg,
        require_action=require_action,
        require_org_action=require_org_action,
    )
    register_v3140_routes(
        app,
        svc=svc,
        cfg=cfg,
        require_action=require_action,
        require_org_action=require_org_action,
    )
    register_v4150_routes(
        app,
        svc=svc,
        cfg=cfg,
        require_action=require_action,
        require_org_action=require_org_action,
    )
