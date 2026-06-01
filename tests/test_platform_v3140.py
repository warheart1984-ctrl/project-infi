"""Platform Membrane v31–v40 tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.proof.bundles import build_attestation_bundle
from platform.proof.federation import register_attestation
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


def test_webhook_subscription_and_emit(client: TestClient):
    org_id = "wh-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "WH"})
    sub = client.post(
        f"/v1/orgs/{org_id}/webhooks",
        headers=h,
        json={"url": "http://127.0.0.1:9/nowhere", "event_types": ["job.status"]},
    )
    assert sub.status_code == 200
    assert sub.json().get("secret")
    lst = client.get(f"/v1/orgs/{org_id}/webhooks", headers=h)
    assert len(lst.json().get("subscriptions", [])) >= 1
    assert "secret" not in lst.json()["subscriptions"][0]
    emit = client.post(f"/v1/orgs/{org_id}/events/emit-test?event_type=job.status", headers=h)
    assert emit.status_code == 200


def test_marketplace_review_and_catalog(client: TestClient):
    org_id = "cat-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Cat"})
    pub = client.post(
        f"/v1/orgs/{org_id}/marketplace/listings",
        headers=h,
        json={
            "org_id": org_id,
            "name": "searchable-pipeline",
            "visibility": "org",
            "steps": [{"subsystem": "lab", "kind": "lab.session"}],
        },
    )
    lid = pub.json()["listing_id"]
    if pub.json().get("approval_status") != "published":
        client.post(f"/v1/marketplace/listings/{lid}/approve", headers=h)
    rev = client.post(
        f"/v1/marketplace/listings/{lid}/reviews?org_id={org_id}",
        headers=h,
        json={"rating": 5, "comment": "good"},
    )
    assert rev.status_code == 200
    cat = client.get(f"/v1/marketplace/catalog?org_id={org_id}&q=searchable", headers=h)
    assert any(x["listing_id"] == lid for x in cat.json().get("listings", []))
    bump = client.patch(
        f"/v1/marketplace/listings/{lid}/version?org_id={org_id}",
        headers=h,
        json={"semver": "1.1.0", "breaking": False},
    )
    assert bump.status_code == 200
    assert bump.json().get("semver") == "1.1.0"


def test_proof_attestation_bundle(client: TestClient):
    org_id = "bundle-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Bundle"})
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    jid = job.json()["job_id"]
    svc = client.app.state.platform_service
    hsh = "c" * 64
    sig = sign_hmac(job_id=jid, runner_id="r1", result_hash=hsh)
    register_attestation(
        store=svc.store,
        job_id=jid,
        runner_id="r1",
        result_hash=hsh,
        signature=sig,
        signature_alg="hmac-sha256",
    )
    bundle = client.get(f"/v1/jobs/{jid}/attestations/bundle", headers=h)
    assert bundle.status_code == 200
    assert bundle.json().get("bundle_version")
    built = build_attestation_bundle(store=svc.store, job_id=jid)
    assert built["job_id"] == jid


def test_mesh_queue_and_compact(client: TestClient):
    org_id = "mesh-v3-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "MeshV3"})
    q = client.put(
        f"/v1/orgs/{org_id}/mesh/queue",
        headers=h,
        json={"principal_ids": ["op-a", "op-b"]},
    )
    assert q.status_code == 200
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    jid = job.json()["job_id"]
    assign = client.post(
        f"/v1/jobs/{jid}/assign?org_id={org_id}",
        headers=h,
        json={"assignee_principal_id": ""},
    )
    assert assign.status_code == 200
    assert assign.json()["assignee_principal_id"] == "op-a"
    compact = client.post(f"/v1/orgs/{org_id}/mesh/compact", headers=h)
    assert compact.status_code == 200


def test_sovereign_compliance_and_exports(client: TestClient):
    tenant = "tenant:sov2"
    h = _h(client)
    client.post(
        "/v1/orgs",
        headers=h,
        json={"org_id": "sov2-a", "label": "A", "ugr_tenant_id": tenant},
    )
    pol = client.put(
        "/v1/orgs/sov2-a/compliance/policy",
        headers=h,
        json={"retention_days": 14, "export_allowed_kinds": ["audit", "attestations"]},
    )
    assert pol.status_code == 200
    usage = client.get("/v1/orgs/sov2-a/exports/usage?from_day=2026-01-01&to_day=2026-12-31", headers=h)
    assert usage.status_code == 200
    summary = client.get(f"/v1/tenants/{tenant}/summary", headers=h)
    assert "webhook_delivery_failures" in summary.json()
