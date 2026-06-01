"""FastAPI ingress for Platform Membrane."""

from __future__ import annotations

import os
import time
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from platform.auth.api_keys import verify_api_key
from platform.auth.oidc import verify_session_token
from platform.auth.rbac import Principal, authorize, authorize_scope, principal_from_resolution
from platform.billing.engine import default_org_billing_fields
from platform.artifacts.signing import sign_download_url
from platform.extra_routes import register_extra_routes
from platform.service import PlatformService
from platform.settings import PlatformSettings


class CreateOrgRequest(BaseModel):
    org_id: str
    label: str = ""
    ugr_tenant_id: str = ""


class CreateApiKeyRequest(BaseModel):
    principal_id: str
    roles: list[str] = Field(default_factory=lambda: ["operator"])
    scopes: list[str] = Field(default_factory=list)
    display_name: str = ""
    principal_kind: str = "service_account"


class CreateJobRequest(BaseModel):
    subsystem: Literal[
        "mechanic",
        "forgekeeper",
        "slingshot",
        "lab",
        "ai_factory",
        "drift_detector",
        "workflow_engine",
    ]
    kind: str
    org_id: str = ""
    subsystem_job_id: str = ""
    correlation_id: str = ""
    parent_job_id: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


class RegisterArtifactRequest(BaseModel):
    org_id: str
    subsystem: Literal["mechanic", "forgekeeper", "slingshot", "lab", "ai_factory"]
    logical_path: str
    storage_uri: str
    sha256: str
    job_id: str = ""
    correlation_id: str = ""
    claim_label: Literal["asserted", "proven", "rejected"] = "asserted"
    lineage_parent_refs: list[str] = Field(default_factory=list)
    ttl_days: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


def create_app(
    *,
    service: PlatformService | None = None,
    settings: PlatformSettings | None = None,
) -> FastAPI:
    cfg = settings or PlatformSettings.from_env()
    svc = service or PlatformService(cfg)
    app = FastAPI(title="Platform Membrane", version="3.0.0")
    app.state.platform_service = svc
    app.state.settings = cfg
    app.state.rate_limit: dict[str, list[float]] = {}

    @app.middleware("http")
    async def hardening_middleware(request: Request, call_next: Any) -> Any:
        if request.url.path == "/v1/health":
            return await call_next(request)
        content_length = int(request.headers.get("content-length") or 0)
        if content_length > cfg.max_request_bytes:
            return JSONResponse({"detail": "request too large"}, status_code=413)
        key = request.headers.get("x-api-key") or (request.client.host if request.client else "unknown")
        now = time.time()
        window = [stamp for stamp in app.state.rate_limit.get(key, []) if now - stamp < 60]
        if len(window) >= cfg.rate_limit_per_minute:
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        window.append(now)
        app.state.rate_limit[key] = window
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    def resolve_principal(
        x_api_key: str = Header(default=""),
        authorization: str = Header(default=""),
    ) -> Principal:
        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            secret = cfg.master_api_key or "platform-session-secret"
            payload = verify_session_token(token, secret=secret)
            if payload:
                org_id = str(payload.get("org_id") or "")
                pid = str(payload.get("principal_id") or "")
                bindings = svc.store.list_role_bindings(org_id=org_id, principal_id=pid)
                roles = [str(b["role"]) for b in bindings] or ["operator"]
                from platform.common import scopes_for_roles

                return Principal(
                    principal_id=pid,
                    org_id=org_id,
                    roles=roles,
                    scopes=scopes_for_roles(roles),
                    display_name=pid,
                )
        if verify_api_key(provided=x_api_key, expected_hash=cfg.master_api_key_hash):
            return Principal(
                principal_id="platform-master",
                org_id="platform",
                roles=["platform_admin"],
                scopes=["*"],
                api_key_id="master",
                display_name="Platform Master",
            )
        resolved = svc.store.resolve_api_key(x_api_key)
        if not resolved:
            if cfg.require_api_key:
                raise HTTPException(status_code=401, detail="invalid api key")
            return Principal(principal_id="anonymous", org_id="default", roles=["read_only"], scopes=["jobs:read"])
        return principal_from_resolution(resolved)

    def require_action(action: str):
        def _dep(principal: Principal = Depends(resolve_principal)) -> Principal:
            if not authorize(principal=principal, action=action, target_org_id=None):
                raise HTTPException(status_code=403, detail="forbidden")
            return principal

        return _dep

    def require_org_action(action: str):
        def _dep(
            org_id: str,
            principal: Principal = Depends(resolve_principal),
        ) -> Principal:
            if not authorize(principal=principal, action=action, target_org_id=org_id):
                raise HTTPException(status_code=403, detail="forbidden")
            return principal

        return _dep

    @app.get("/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "platform-membrane"}

    @app.post("/v1/orgs")
    def create_org(
        body: CreateOrgRequest,
        principal: Principal = Depends(require_action("org.create")),
    ) -> dict[str, Any]:
        bootstrap_pid = f"principal-{body.org_id}-owner"
        payload = {
            "org_id": body.org_id,
            "label": body.label or body.org_id,
            "ugr_tenant_id": body.ugr_tenant_id or f"tenant:{body.org_id}",
            "plan_id": "free",
            "region": "us",
            "data_residency": "us",
            "tenant_id": body.org_id,
            **default_org_billing_fields(owner_principal_id=bootstrap_pid),
        }
        svc.store.upsert_org(payload)
        svc.store.upsert_principal(
            {
                "principal_id": bootstrap_pid,
                "org_id": body.org_id,
                "roles": ["owner"],
                "principal_kind": "human",
                "display_name": f"{body.org_id} owner",
            }
        )
        svc.store.upsert_role_binding(
            org_id=body.org_id,
            principal_id=bootstrap_pid,
            role="owner",
            granted_by=principal.principal_id,
        )
        return payload

    @app.get("/v1/orgs/{org_id}")
    def get_org(
        org_id: str,
        principal: Principal = Depends(require_org_action("org.read")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="org not found")
        return org

    @app.post("/v1/orgs/{org_id}/api-keys")
    def create_api_key(
        org_id: str,
        body: CreateApiKeyRequest,
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
        return {
            "api_key": raw,
            "api_key_id": api_key_id,
            "scopes": rec.get("scopes"),
            "org_id": org_id,
            "principal_id": body.principal_id,
        }

    @app.get("/v1/principals/me")
    def principals_me(principal: Principal = Depends(require_action("principal.read"))) -> dict[str, Any]:
        return principal.model_dump()

    @app.post("/v1/jobs")
    def create_job(
        body: CreateJobRequest,
        principal: Principal = Depends(require_action("job.create")),
    ) -> dict[str, Any]:
        if not authorize_scope(principal=principal, scope="jobs:submit"):
            raise HTTPException(status_code=403, detail="missing jobs:submit scope")
        target_org = body.org_id or principal.org_id
        if body.org_id and body.org_id != principal.org_id and not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="forbidden org")
        job_principal = principal
        if body.org_id and principal.is_platform_admin():
            job_principal = Principal(
                principal_id=principal.principal_id,
                org_id=body.org_id,
                roles=list(principal.roles),
                scopes=list(principal.scopes),
                api_key_id=principal.api_key_id,
            )
        try:
            job = svc.jobs.create_job(
                principal=job_principal,
            subsystem=body.subsystem,
            kind=body.kind,
            params=body.params,
            subsystem_job_id=body.subsystem_job_id,
            correlation_id=body.correlation_id,
            parent_job_id=body.parent_job_id,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if not svc.settings.redis_url:
            from platform.adapters.dispatch import dispatch_job

            dispatch_job(
                registry=svc.jobs,
                artifact_index=svc.artifacts,
                principal=job_principal,
                job=job,
            )
        return job

    @app.get("/v1/jobs/{job_id}")
    def get_job(
        job_id: str,
        principal: Principal = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        job = svc.jobs.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        if job.get("org_id") != principal.org_id and not principal.is_platform_admin():
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @app.get("/v1/jobs")
    def list_jobs(
        org_id: str,
        subsystem: str = "",
        status: str = "",
        correlation_id: str = "",
        job_type: str = "",
        proof_status: str = "",
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        if org_id != principal.org_id and not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="forbidden")
        return {
            "jobs": svc.jobs.list_jobs(
                org_id=org_id,
                subsystem=subsystem,
                status=status,
                correlation_id=correlation_id,
                job_type=job_type,
                proof_status=proof_status,
            )
        }

    @app.post("/v1/jobs/{job_id}/cancel")
    def cancel_job(
        job_id: str,
        principal: Principal = Depends(require_action("job.cancel")),
    ) -> dict[str, Any]:
        job = svc.jobs.cancel_job(principal=principal, job_id=job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @app.post("/v1/artifacts")
    def register_artifact(
        body: RegisterArtifactRequest,
        principal: Principal = Depends(require_action("artifact.register")),
    ) -> dict[str, Any]:
        if not authorize(principal=principal, action="artifact.register", target_org_id=body.org_id):
            raise HTTPException(status_code=403, detail="forbidden")
        ref = svc.artifacts.build_ref(
            org_id=body.org_id,
            subsystem=body.subsystem,
            logical_path=body.logical_path,
            storage_uri=body.storage_uri,
            sha256=body.sha256,
            job_id=body.job_id,
            correlation_id=body.correlation_id,
            claim_label=body.claim_label,
            lineage_parent_refs=body.lineage_parent_refs,
            ttl_days=body.ttl_days,
            metadata=body.metadata,
        )
        try:
            return svc.artifacts.register(principal=principal, payload=ref)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/v1/artifacts/{ref_id}")
    def get_artifact(
        ref_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("artifact.read")),
    ) -> dict[str, Any]:
        ref = svc.artifacts.get_ref(
            ref_id,
            org_id=org_id,
            platform_admin=principal.is_platform_admin(),
        )
        if not ref:
            raise HTTPException(status_code=404, detail="artifact not found")
        secret = cfg.master_api_key or "artifact-signing-secret"
        ref = dict(ref)
        ref["download_url"] = sign_download_url(
            ref_id=str(ref["ref_id"]),
            storage_uri=str(ref.get("storage_uri") or ""),
            secret=secret,
        )
        ref["produced_by_job"] = ref.get("job_id")
        return ref

    @app.get("/v1/artifacts/{ref_id}/lineage")
    def artifact_lineage(
        ref_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("artifact.read")),
    ) -> dict[str, Any]:
        return svc.artifacts.lineage(
            ref_id,
            org_id=org_id,
            platform_admin=principal.is_platform_admin(),
        )

    @app.get("/v1/artifacts")
    def list_artifacts(
        org_id: str,
        subsystem: str = "",
        correlation_id: str = "",
        job_id: str = "",
        artifact_type: str = "",
        visibility: str = "",
        principal: Principal = Depends(require_org_action("artifact.read")),
    ) -> dict[str, Any]:
        return {
            "artifacts": svc.artifacts.list_refs(
                org_id=org_id,
                subsystem=subsystem,
                correlation_id=correlation_id,
                job_id=job_id,
                artifact_type=artifact_type,
                visibility=visibility,
            )
        }

    @app.get("/v1/audit")
    def list_audit(
        org_id: str,
        limit: int = 50,
        principal: Principal = Depends(require_org_action("audit.read")),
    ) -> dict[str, Any]:
        return {"events": svc.store.list_audit(org_id=org_id, limit=limit)}

    register_extra_routes(
        app,
        svc=svc,
        cfg=cfg,
        resolve_principal=resolve_principal,
        require_action=require_action,
        require_org_action=require_org_action,
    )

    return app
