"""Platform Membrane v8–v14 API routes."""

from __future__ import annotations

import os
import secrets
from typing import Any

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from platform.assistant.query import run_assistant_query
from platform.auth.audit import append_audit_event
from platform.auth.oidc import issue_session_token
from platform.auth.oidc_providers import build_authorize_url, exchange_code_for_identity, provider_from_org
from platform.auth.rbac import Principal, authorize_scope
from platform.billing.engine import billing_period_csv, close_billing_period, evaluate_billing_gate
from platform.common import new_id
from platform.policy.compile import compile_rules
from platform.service import PlatformService
from platform.settings import PlatformSettings
from platform.workflow.engine import start_workflow_run
from platform.workflow.schema import build_workflow


class AssistantQueryRequest(BaseModel):
    org_id: str
    question: str
    job_id: str = ""


class PolicyDslRequest(BaseModel):
    rules_source: str


class WorkflowCreateRequest(BaseModel):
    name: str
    steps: list[dict[str, str]] = Field(default_factory=list)


class BillingStatusRequest(BaseModel):
    billing_status: str


def register_v814_routes(
    app: Any,
    *,
    svc: PlatformService,
    cfg: PlatformSettings,
    resolve_principal: Any,
    require_action: Any,
    require_org_action: Any,
) -> None:

    @app.post("/v1/auth/token/refresh")
    def token_refresh(
        org_id: str,
        principal_id: str,
        principal: Principal = Depends(require_org_action("org.read")),
    ) -> dict[str, str]:
        secret = cfg.master_api_key or "platform-session-secret"
        token = issue_session_token(org_id=org_id, principal_id=principal_id or principal.principal_id, secret=secret)
        return {"access_token": token}

    @app.get("/v1/orgs/{org_id}/billing")
    def org_billing(
        org_id: str,
        principal: Principal = Depends(require_org_action("org.read")),
    ) -> dict[str, Any]:
        if not authorize_scope(principal=principal, scope="org:billing", target_org_id=org_id):
            raise HTTPException(status_code=403, detail="forbidden")
        org = svc.store.get_org(org_id)
        periods = svc.store.list_billing_periods(org_id=org_id)
        ok, reason = evaluate_billing_gate(org)
        return {"org": org, "periods": periods, "gate_ok": ok, "gate_reason": reason}

    @app.post("/v1/orgs/{org_id}/billing/close")
    def close_billing(
        org_id: str,
        period: str = "",
        principal: Principal = Depends(require_org_action("org.billing")),
    ) -> dict[str, Any]:
        return close_billing_period(store=svc.store, org_id=org_id, period=period or None)

    @app.get("/v1/orgs/{org_id}/billing/export")
    def billing_export(
        org_id: str,
        period: str = "",
        principal: Principal = Depends(require_org_action("org.billing")),
    ) -> Any:
        from fastapi.responses import PlainTextResponse

        org = svc.store.get_org(org_id) or {}
        p = period or str(org.get("billing_cycle_start", ""))[:7]
        return PlainTextResponse(billing_period_csv(store=svc.store, org_id=org_id, period=p))

    @app.patch("/v1/orgs/{org_id}/billing/status")
    def set_billing_status(
        org_id: str,
        body: BillingStatusRequest,
        principal: Principal = Depends(require_org_action("org.billing")),
    ) -> dict[str, Any]:
        org = svc.store.get_org(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="org not found")
        org["billing_status"] = body.billing_status
        svc.store.upsert_org(org)
        return org

    @app.put("/v1/orgs/{org_id}/policies")
    def put_policies(
        org_id: str,
        body: PolicyDslRequest,
        principal: Principal = Depends(require_org_action("org.admin")),
    ) -> dict[str, Any]:
        _, compiled_hash, records = compile_rules(org_id=org_id, source=body.rules_source)
        svc.store.delete_policy_rules(org_id=org_id)
        for rec in records:
            svc.store.upsert_policy_rule(rec)
        org = svc.store.get_org(org_id) or {"org_id": org_id}
        org["policy_dsl"] = {"rules_source": body.rules_source, "compiled_hash": compiled_hash}
        svc.store.upsert_org(org)
        if cfg.audit_path:
            append_audit_event(
                audit_path=cfg.audit_path,
                org_id=org_id,
                principal_id=principal.principal_id,
                action="policy.update",
                details={"compiled_hash": compiled_hash},
                store=svc.store,
            )
        return {"org_id": org_id, "compiled_hash": compiled_hash, "rules": records}

    @app.get("/v1/orgs/{org_id}/policies")
    def get_policies(
        org_id: str,
        principal: Principal = Depends(require_org_action("org.read")),
    ) -> dict[str, Any]:
        return {"rules": svc.store.list_policy_rules(org_id=org_id, enabled_only=False)}

    @app.post("/v1/assistant/query")
    def assistant_query(
        body: AssistantQueryRequest,
        principal: Principal = Depends(require_action("job.read")),
    ) -> dict[str, Any]:
        if body.org_id != principal.org_id and not principal.is_platform_admin():
            raise HTTPException(status_code=403, detail="forbidden")
        if not authorize_scope(principal=principal, scope="jobs:read", target_org_id=body.org_id):
            raise HTTPException(status_code=403, detail="forbidden")
        result = run_assistant_query(
            store=svc.store,
            org_id=body.org_id,
            question=body.question,
            job_id=body.job_id,
        )
        if cfg.audit_path:
            append_audit_event(
                audit_path=cfg.audit_path,
                org_id=body.org_id,
                principal_id=principal.principal_id,
                action="assistant.query",
                details={"job_id": body.job_id},
                store=svc.store,
            )
        return result

    @app.get("/v1/orgs/{org_id}/drift/jobs")
    def list_drift_jobs(
        org_id: str,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        jobs = svc.store.list_jobs(org_id=org_id, subsystem="drift_detector")
        return {"jobs": jobs}

    @app.post("/v1/workflows")
    def create_workflow(
        org_id: str,
        body: WorkflowCreateRequest,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, Any]:
        wf = build_workflow(org_id=org_id, name=body.name, steps=body.steps)
        svc.store.upsert_workflow(wf)
        return wf

    @app.get("/v1/workflows")
    def list_workflows(
        org_id: str,
        principal: Principal = Depends(require_org_action("job.read")),
    ) -> dict[str, Any]:
        return {"workflows": svc.store.list_workflows(org_id=org_id)}

    @app.post("/v1/workflows/{workflow_id}/run")
    def run_workflow(
        workflow_id: str,
        org_id: str,
        principal: Principal = Depends(require_org_action("job.create")),
    ) -> dict[str, Any]:
        wf = svc.store.get_workflow(workflow_id)
        if not wf or wf.get("org_id") != org_id:
            raise HTTPException(status_code=404, detail="workflow not found")
        job = start_workflow_run(
            store=svc.store,
            org_id=org_id,
            workflow=wf,
            actor_principal_id=principal.principal_id,
            enqueue=lambda jid, region="us": svc.queue.enqueue(jid, region=region),
        )
        return {"workflow_run": job}


def patch_oidc_routes(app: Any, *, svc: PlatformService, cfg: PlatformSettings) -> None:
    """Replace scaffold OIDC handlers with v8 provider registry."""

    @app.get("/v1/auth/oidc/{org_id}/login")
    def oidc_login_v8(org_id: str) -> dict[str, str]:
        org = svc.store.get_org(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="org not found")
        provider = provider_from_org(org)
        cfg_oidc = dict(org.get("oidc_config") or org.get("oidc") or {})
        state = secrets.token_hex(8)
        redirect_uri = os.environ.get("PLATFORM_OIDC_REDIRECT_URI", "http://127.0.0.1:8090/v1/auth/oidc/callback")
        url = build_authorize_url(
            provider=provider,
            client_id=str(cfg_oidc.get("client_id") or os.environ.get(f"PLATFORM_OIDC_{provider.upper()}_CLIENT_ID", "")),
            redirect_uri=redirect_uri,
            state=state,
            org_id=org_id,
        )
        return {"login_url": url, "state": state, "provider": provider}

    @app.get("/v1/auth/oidc/callback")
    def oidc_callback_v8(org_id: str, code: str = "", state: str = "") -> dict[str, Any]:
        org = svc.store.get_org(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="org not found")
        provider = provider_from_org(org)
        identity = exchange_code_for_identity(provider=provider, code=code, org=org)
        pid = f"oidc-{org_id}-{identity.get('sub', 'user')}"
        svc.store.upsert_principal(
            {
                "principal_id": pid,
                "org_id": org_id,
                "roles": ["operator"],
                "principal_kind": "human",
                "display_name": identity.get("email", pid),
            }
        )
        secret = cfg.master_api_key or "platform-session-secret"
        token = issue_session_token(org_id=org_id, principal_id=pid, secret=secret)
        return {"access_token": token, "principal_id": pid, "org_id": org_id, "provider": provider}
