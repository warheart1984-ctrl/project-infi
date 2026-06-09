"""Platform Membrane v8–v14 integration tests."""

from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from platform.api import create_app
from platform.billing.engine import evaluate_billing_gate
from platform.policy.compile import compile_rules, evaluate_compiled_rules, build_admission_context
from platform.service import PlatformService
from platform.settings import PlatformSettings


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    from platform.auth.api_keys import hash_api_key

    master = "test-master-key"
    settings = PlatformSettings(
        sqlite_path=tmp_path / "platform.sqlite3",
        audit_path=tmp_path / "audit.jsonl",
        runtime_root=tmp_path / "runtime",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        require_api_key=True,
        redis_url="",
    )
    svc = PlatformService(settings)
    app = create_app(service=svc, settings=settings)
    c = TestClient(app)
    c.headers = {"X-Api-Key": master}
    return c


def _h(client: TestClient) -> dict[str, str]:
    return getattr(client, "headers", {"X-Api-Key": "test-master-key"})


def test_billing_gate_blocks_suspended():
    ok, _ = evaluate_billing_gate({"billing_status": "active"})
    assert ok
    ok2, reason = evaluate_billing_gate({"billing_status": "suspended"})
    assert not ok2
    assert "suspended" in reason


def test_policy_dsl_deny_mechanic_scan(client: TestClient):
    org_id = "dsl-test-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "DSL Test"})
    rules = 'deny mechanic.scan when job_type == "scan" and org_plan_id == "free"'
    client.put(f"/v1/orgs/{org_id}/policies", headers=h, json={"rules_source": rules})
    resp = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "mechanic", "kind": "mechanic.scan", "params": {}},
    )
    assert resp.status_code == 403
    assert "deny" in resp.json().get("detail", "").lower() or "policy" in resp.json().get("detail", "").lower()


def test_billing_suspended_blocks_job(client: TestClient):
    org_id = "bill-block-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Bill"})
    client.patch(f"/v1/orgs/{org_id}/billing/status", headers=h, json={"billing_status": "suspended"})
    resp = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    assert resp.status_code == 403


def test_assistant_query_read_only(client: TestClient):
    org_id = "asst-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Asst"})
    r = client.post(
        "/v1/assistant/query",
        headers=h,
        json={"org_id": org_id, "question": "status?", "job_id": ""},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("claim_label") == "asserted"
    assert "summary" in body


def test_assistant_cannot_import_job_registry():
    mod = importlib.import_module("platform.assistant.query")
    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "JobRegistry" not in source
    assert "create_job" not in source


def test_region_queue_key():
    from platform.jobs.queue import queue_key_for_region

    assert queue_key_for_region("eu") == "platform:jobs:eu"


def test_proof_required_on_factory_kind():
    from platform.jobs.schema import build_job_record

    job = build_job_record(
        org_id="o",
        subsystem="ai_factory",
        kind="ai_factory.build",
        actor_principal_id="p",
    )
    assert job.get("proof_required") is True


def test_workflow_run(client: TestClient):
    org_id = "wf-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "WF"})
    wf = client.post(
        f"/v1/workflows?org_id={org_id}",
        headers=h,
        json={
            "name": "scan-preload-lab",
            "steps": [
                {"subsystem": "mechanic", "kind": "mechanic.scan"},
                {"subsystem": "slingshot", "kind": "slingshot.preload"},
                {"subsystem": "lab", "kind": "lab.session"},
            ],
        },
    )
    assert wf.status_code == 200
    wid = wf.json()["workflow_id"]
    run = client.post(f"/v1/workflows/{wid}/run?org_id={org_id}", headers=h)
    assert run.status_code == 200
    assert run.json()["workflow_run"]["kind"] == "workflow_run"


def test_drift_jobs_list(client: TestClient):
    org_id = "drift-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Drift"})
    r = client.get(f"/v1/orgs/{org_id}/drift/jobs", headers=h)
    assert r.status_code == 200
    assert "jobs" in r.json()


def test_policy_compile_require_proof():
    predicates, _, _ = compile_rules(
        org_id="x",
        source='require proof when job_proof_status != "proven"',
    )
    ctx = build_admission_context(
        org={"org_id": "x", "plan_id": "pro"},
        job_request={"kind": "ai_factory.build", "proof_status": "asserted"},
    )
    ok, _ = evaluate_compiled_rules(predicates, ctx=ctx)
    assert not ok


def test_oidc_stub_org_e2e(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """One org authorize → callback → session token (stub IdP, PLAT-D8 proof path)."""
    monkeypatch.setenv("PLATFORM_OIDC_STUB", "1")
    org_id = "oidc-e2e-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "OIDC E2E"})
    org = client.get(f"/v1/orgs/{org_id}", headers=h).json()
    org["oidc_provider"] = "github"
    org["oidc_config"] = {"client_id": "test-client-id"}
    client.app.state.platform_service.store.upsert_org(org)

    login = client.get(f"/v1/auth/oidc/{org_id}/login")
    assert login.status_code == 200
    body = login.json()
    assert body.get("provider") == "github"
    assert "login_url" in body

    callback = client.get(
        f"/v1/auth/oidc/callback",
        params={"org_id": org_id, "code": "stub-auth-code", "state": body.get("state", "")},
    )
    assert callback.status_code == 200
    session = callback.json()
    assert session.get("org_id") == org_id
    assert session.get("principal_id", "").startswith(f"oidc-{org_id}-")
    assert session.get("access_token")
