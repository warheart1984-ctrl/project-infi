"""Platform Membrane v15–v20 tests."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.service import PlatformService
from platform.settings import PlatformSettings


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
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


def test_mesh_presence_and_assign(client: TestClient):
    org_id = "mesh-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Mesh"})
    client.post(
        f"/v1/orgs/{org_id}/mesh/presence",
        headers=h,
        json={"status": "online", "session_id": "s1"},
    )
    ops = client.get(f"/v1/orgs/{org_id}/mesh/operators", headers=h)
    assert ops.status_code == 200
    assert len(ops.json().get("operators", [])) >= 1
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    jid = job.json()["job_id"]
    assign = client.post(
        f"/v1/jobs/{jid}/assign?org_id={org_id}",
        headers=h,
        json={"assignee_principal_id": "operator-b"},
    )
    assert assign.status_code == 200
    assert assign.json()["assignee_principal_id"] == "operator-b"


def test_on_call_and_handoff(client: TestClient):
    org_id = "handoff-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "HO"})
    client.put(
        f"/v1/orgs/{org_id}/on-call",
        headers=h,
        json={"principal_ids": ["oncall-1"]},
    )
    cur = client.get(f"/v1/orgs/{org_id}/on-call/current", headers=h)
    assert cur.json()["principal_id"] == "oncall-1"
    handoff = client.post(
        f"/v1/orgs/{org_id}/mesh/handoff",
        headers=h,
        json={"to_principal_id": "oncall-2", "notes": "shift"},
    )
    assert handoff.status_code == 200
    assert "bundle_id" in handoff.json()


def test_marketplace_org_visibility(client: TestClient):
    org_id = "mkt-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Mkt"})
    pub = client.post(
        f"/v1/orgs/{org_id}/marketplace/listings",
        headers=h,
        json={
            "org_id": org_id,
            "name": "scan-pipeline",
            "visibility": "org",
            "steps": [{"subsystem": "mechanic", "kind": "mechanic.scan"}],
        },
    )
    assert pub.status_code == 200
    lst = client.get(f"/v1/marketplace/listings?org_id={org_id}", headers=h)
    assert any(x["listing_id"] == pub.json()["listing_id"] for x in lst.json()["listings"])


def test_marketplace_tenant_visibility(client: TestClient):
    h = _h(client)
    tenant = "tenant:shared"
    client.post(
        "/v1/orgs",
        headers=h,
        json={"org_id": "org-a", "label": "A", "ugr_tenant_id": tenant},
    )
    client.post(
        "/v1/orgs",
        headers=h,
        json={"org_id": "org-b", "label": "B", "ugr_tenant_id": tenant},
    )
    pub = client.post(
        "/v1/orgs/org-a/marketplace/listings",
        headers=h,
        json={
            "org_id": "org-a",
            "name": "tenant-wf",
            "visibility": "tenant",
            "steps": [{"subsystem": "lab", "kind": "lab.session"}],
        },
    )
    lid = pub.json()["listing_id"]
    lst_b = client.get("/v1/marketplace/listings?org_id=org-b", headers=h)
    assert any(x["listing_id"] == lid for x in lst_b.json()["listings"])


def test_marketplace_install_and_run(client: TestClient):
    org_id = "run-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Run"})
    pub = client.post(
        f"/v1/orgs/{org_id}/marketplace/listings",
        headers=h,
        json={
            "org_id": org_id,
            "name": "three-step",
            "visibility": "org",
            "steps": [
                {"subsystem": "mechanic", "kind": "mechanic.scan"},
                {"subsystem": "slingshot", "kind": "slingshot.preload"},
                {"subsystem": "lab", "kind": "lab.session"},
            ],
        },
    )
    lid = pub.json()["listing_id"]
    inst = client.post(f"/v1/marketplace/listings/{lid}/install?org_id={org_id}", headers=h)
    assert inst.status_code == 200
    run = client.post(f"/v1/marketplace/listings/{lid}/run?org_id={org_id}", headers=h)
    assert run.status_code == 200
    assert run.json()["workflow_run"]["kind"] == "workflow_run"


def test_proof_attestation_quorum(client: TestClient):
    from platform.proof.federation import register_attestation
    from platform.proof.quorum import evaluate_quorum

    org_id = "proof-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Proof"})
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    jid = job.json()["job_id"]
    svc = client.app.state.platform_service
    j = svc.store.get_job(jid)
    assert j is not None
    j["proof_required"] = True
    j["proof_status"] = "asserted"
    svc.store.upsert_job(j)
    hsh = "deadbeef" * 8
    for rid in ("r1", "r2"):
        register_attestation(store=svc.store, job_id=jid, runner_id=rid, result_hash=hsh)
    updated, ok = evaluate_quorum(store=svc.store, job=j)
    assert ok
    assert updated.get("proof_status") == "proven"
    fed = client.get(f"/v1/proof/federation/{jid}", headers=h)
    assert fed.json().get("quorum_met") is True


def test_mesh_no_job_registry_import():
    for name in ("assignment", "presence", "handoff", "on_call"):
        mod = importlib.import_module(f"platform.mesh.{name}")
        text = Path(mod.__file__).read_text(encoding="utf-8")
        assert "JobRegistry" not in text
        assert "create_job" not in text
