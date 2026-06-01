"""Platform Membrane v21–v30 tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.proof.signing import sign_hmac
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


def test_mesh_policy_and_events(client: TestClient):
    org_id = "mesh-v2-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "MeshV2"})
    pol = client.put(
        f"/v1/orgs/{org_id}/mesh/policy",
        headers=h,
        json={"max_assignments_per_operator": 5, "require_on_call_for_drift_investigation": False},
    )
    assert pol.status_code == 200
    getp = client.get(f"/v1/orgs/{org_id}/mesh/policy", headers=h)
    assert getp.json()["mesh_policy"]["max_assignments_per_operator"] == 5
    client.post(f"/v1/orgs/{org_id}/mesh/presence", headers=h, json={"status": "online"})
    ev = client.get(f"/v1/orgs/{org_id}/mesh/events", headers=h)
    assert ev.status_code == 200


def test_handoff_runbook_ref(client: TestClient):
    org_id = "rb-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "RB"})
    handoff = client.post(
        f"/v1/orgs/{org_id}/mesh/handoff",
        headers=h,
        json={
            "to_principal_id": "op-2",
            "notes": "go",
            "runbook_ref": "docs/subsystems/platform/OPERATIONAL_RUNBOOK.md#drift",
        },
    )
    assert handoff.status_code == 200
    assert "OPERATIONAL_RUNBOOK" in handoff.json().get("runbook_ref", "")


def test_marketplace_approval_and_analytics(client: TestClient):
    org_id = "mkt-v2"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "MktV2"})
    pub = client.post(
        f"/v1/orgs/{org_id}/marketplace/listings",
        headers=h,
        json={
            "org_id": org_id,
            "name": "wf",
            "visibility": "org",
            "steps": [{"subsystem": "lab", "kind": "lab.session"}],
        },
    )
    lid = pub.json()["listing_id"]
    assert pub.json().get("approval_status") in {"published", "draft"}
    if pub.json().get("approval_status") != "published":
        appr = client.post(f"/v1/marketplace/listings/{lid}/approve", headers=h)
        assert appr.status_code == 200
    inst = client.post(f"/v1/marketplace/listings/{lid}/install?org_id={org_id}", headers=h)
    assert inst.status_code == 200
    analytics = client.get(f"/v1/orgs/{org_id}/marketplace/analytics", headers=h)
    assert analytics.status_code == 200
    assert analytics.json().get("marketplace_installs", 0) >= 1
    dep = client.post(
        f"/v1/marketplace/listings/{lid}/deprecate?org_id={org_id}",
        headers=h,
        json={},
    )
    assert dep.status_code == 200
    blocked = client.post(f"/v1/marketplace/listings/{lid}/install?org_id={org_id}", headers=h)
    assert blocked.status_code == 403


def test_signed_attestation_and_dispute(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    org_id = "proof-v2"
    h = _h(client)
    monkeypatch.setenv("PLATFORM_ATTESTATION_SECRET", "test-secret")
    monkeypatch.setenv("PLATFORM_ATTESTATION_ALG", "hmac-sha256")
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "ProofV2"})
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    jid = job.json()["job_id"]
    svc = client.app.state.platform_service
    j = svc.store.get_job(jid)
    j["proof_required"] = True
    svc.store.upsert_job(j)
    sig1 = sign_hmac(job_id=jid, runner_id="r1", result_hash="a" * 64)
    sig2 = sign_hmac(job_id=jid, runner_id="r2", result_hash="b" * 64)
    r1 = client.post(
        f"/v1/jobs/{jid}/attestations",
        headers=h,
        json={"runner_id": "r1", "result_hash": "a" * 64, "signature": sig1},
    )
    r2 = client.post(
        f"/v1/jobs/{jid}/attestations",
        headers=h,
        json={"runner_id": "r2", "result_hash": "b" * 64, "signature": sig2},
    )
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    updated = svc.store.get_job(jid)
    assert updated is not None
    assert updated.get("proof_status") == "disputed"


def test_runner_enroll(client: TestClient):
    h = _h(client)
    en = client.post(
        "/v1/proof/runners/enroll",
        headers=h,
        json={"runner_id": "ci-primary", "region": "us"},
    )
    assert en.status_code == 200
    lst = client.get("/v1/proof/runners", headers=h)
    assert any(r.get("runner_id") == "ci-primary" for r in lst.json().get("runners", []))


def test_sovereign_exports_and_tenant_summary(client: TestClient):
    tenant = "tenant:sov"
    h = _h(client)
    client.post(
        "/v1/orgs",
        headers=h,
        json={"org_id": "sov-a", "label": "A", "ugr_tenant_id": tenant},
    )
    client.post(
        "/v1/orgs",
        headers=h,
        json={"org_id": "sov-b", "label": "B", "ugr_tenant_id": tenant},
    )
    audit = client.get("/v1/orgs/sov-a/exports/audit?format=csv", headers=h)
    assert audit.status_code == 200
    att = client.get("/v1/orgs/sov-a/exports/attestations", headers=h)
    assert att.status_code == 200
    summary = client.get(f"/v1/tenants/{tenant}/summary", headers=h)
    assert summary.status_code == 200
    assert summary.json().get("org_count") == 2


def test_replay_v2_manifest(tmp_path: Path):
    manifest = {
        "manifest_version": "platform.platform_replay_manifest.v2",
        "operational_status": "active",
        "runners": [
            {
                "runner_id": "t1",
                "commands": {"noop": "python -c \"print(1)\""},
            }
        ],
    }
    path = tmp_path / "replay.v2.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    from platform.replay import run_replay

    code = run_replay(manifest_path=path)
    assert code == 0
    report = tmp_path / ".runtime" / "platform" / "replay" / "platform_replay_report.v2.json"
    if not report.exists():
        report = Path(".runtime/platform/replay/platform_replay_report.v2.json")
    assert report.is_file()
