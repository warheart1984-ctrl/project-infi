"""Platform Membrane v41–v50 tests (Sixth arc)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.exchange.envelope import verify_envelope
from platform.exchange.peer import apply_inbound
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


def test_ledger_audit_and_usage_kinds(client: TestClient, tmp_path: Path):
    from platform.auth.audit import append_audit_event
    from platform.billing.aggregator import record_job_completion

    org_id = "led-kinds-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "LedKinds"})
    svc = client.app.state.platform_service
    append_audit_event(
        audit_path=tmp_path / "audit.jsonl",
        org_id=org_id,
        principal_id="admin",
        action="test.audit",
        store=svc.store,
    )
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    ).json()
    j = svc.store.get_job(job["job_id"])
    j["status"] = "complete"
    svc.store.upsert_job(j)
    record_job_completion(store=svc.store, job=j)
    audit_q = client.get(f"/v1/orgs/{org_id}/ledger/query?kind=audit.event", headers=h)
    usage_q = client.get(f"/v1/orgs/{org_id}/ledger/query?kind=usage.rollup", headers=h)
    assert any(e.get("kind") == "audit.event" for e in audit_q.json().get("entries", []))
    assert any(e.get("kind") == "usage.rollup" for e in usage_q.json().get("entries", []))


def test_ledger_chain_and_query(client: TestClient):
    org_id = "led-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Ledger"})
    run = client.post(f"/v1/orgs/{org_id}/mesh/autopilot/run?mode=dry_run", headers=h)
    assert run.status_code == 200
    q = client.get(f"/v1/orgs/{org_id}/ledger/query", headers=h)
    assert q.status_code == 200
    assert len(q.json().get("entries", [])) >= 1
    v = client.get(f"/v1/orgs/{org_id}/ledger/verify", headers=h)
    assert v.json().get("valid") is True


def test_witness_enroll_and_graph(client: TestClient):
    org_id = "wit-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Witness"})
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session", "proof_required": True},
    )
    job_id = job.json()["job_id"]
    en = client.post(
        "/v1/proof/witnesses/enroll",
        headers=h,
        json={"witness_id": "ci-witness-1", "region": "us"},
    )
    assert en.status_code == 200
    rh = "abc123witness"
    sig = sign_hmac(job_id=job_id, runner_id="witness:ci-witness-1", result_hash=rh)
    att = client.post(
        "/v1/proof/witnesses/attest",
        headers=h,
        json={"job_id": job_id, "witness_id": "ci-witness-1", "result_hash": rh, "signature": sig},
    )
    assert att.status_code == 200
    graph = client.get(f"/v1/proof/network/graph?job_id={job_id}", headers=h)
    assert graph.status_code == 200
    assert graph.json().get("witness_count", 0) >= 1


def test_witness_required_blocks_promotion(client: TestClient, monkeypatch):
    from platform.proof.federation import register_attestation
    from platform.proof.quorum import evaluate_quorum, federation_blocks_workflow_step
    from platform.proof.witnesses import enroll_witness

    monkeypatch.setenv("PLATFORM_WITNESS_REQUIRED", "1")
    monkeypatch.setenv("PLATFORM_WITNESS_QUORUM", "1")
    monkeypatch.setenv("PLATFORM_PROOF_QUORUM", "2")

    org_id = "wit-req-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "WitReq"})
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    jid = job.json()["job_id"]
    svc = client.app.state.platform_service
    j = svc.store.get_job(jid)
    j["proof_required"] = True
    j["proof_status"] = "asserted"
    svc.store.upsert_job(j)
    enroll_witness(store=svc.store, witness_id="w-req", region="us")
    hsh = "cafebabe" * 8
    for rid in ("r1", "r2"):
        register_attestation(store=svc.store, job_id=jid, runner_id=rid, result_hash=hsh)
    updated, ok = evaluate_quorum(store=svc.store, job=j)
    assert not ok
    assert updated.get("proof_status") != "proven"
    sig = sign_hmac(job_id=jid, runner_id="witness:w-req", result_hash=hsh)
    register_attestation(
        store=svc.store,
        job_id=jid,
        runner_id="",
        result_hash=hsh,
        witness_id="w-req",
        signature=sig,
    )
    updated, ok = evaluate_quorum(store=svc.store, job=svc.store.get_job(jid) or j)
    assert ok
    assert updated.get("proof_status") == "proven"
    child = dict(j)
    child["parent_job_id"] = jid
    child["job_id"] = "child-job"
    child["proof_required"] = False
    ok_step, reason = federation_blocks_workflow_step(
        store=svc.store,
        job=child,
        next_kind="slingshot.launch",
    )
    assert ok_step


def test_autopilot_webhook_only_on_apply(client: TestClient, monkeypatch):
    delivered: list[str] = []

    def _fake_deliver(*, event_type: str, **kwargs):
        delivered.append(event_type)
        return {"status": "delivered", "delivery_id": "d1", "org_id": kwargs["subscription"].get("org_id")}

    monkeypatch.setattr("platform.events.dispatch.deliver_webhook", _fake_deliver)

    org_id = "wh-auto-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "WhAuto"})
    client.post(
        f"/v1/orgs/{org_id}/webhooks",
        headers=h,
        json={"url": "http://127.0.0.1:9/nowhere", "event_types": ["mesh.autopilot"]},
    )
    client.put(
        f"/v1/orgs/{org_id}/mesh/routing-policy",
        headers=h,
        json={"auto_assign_from_queue": True, "max_auto_assignments_per_run": 1},
    )
    client.put(
        f"/v1/orgs/{org_id}/mesh/queue",
        headers=h,
        json={"principal_ids": ["op-a"]},
    )
    client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    delivered.clear()
    client.post(f"/v1/orgs/{org_id}/mesh/autopilot/run?mode=dry_run", headers=h)
    assert delivered == []
    client.post(f"/v1/orgs/{org_id}/mesh/autopilot/run?mode=apply", headers=h)
    assert "mesh.autopilot" in delivered


def test_autopilot_dry_run_mesh_policy_preview(client: TestClient):
    org_id = "pol-prev-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "PolPrev"})
    svc = client.app.state.platform_service
    org = svc.store.get_org(org_id) or {}
    org["mesh_policy"] = {"max_assignments_per_operator": 1}
    org["assignment_queue"] = ["op-a"]
    org["routing_policy"] = {"auto_assign_from_queue": True}
    svc.store.upsert_org(org)
    j1 = client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    ).json()["job_id"]
    svc.store.upsert_job(
        {**(svc.store.get_job(j1) or {}), "assignee_principal_id": "op-a", "status": "running"}
    )
    client.post(
        "/v1/jobs",
        headers=h,
        json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
    )
    run = client.post(f"/v1/orgs/{org_id}/mesh/autopilot/run?mode=dry_run", headers=h)
    assigns = [a for a in run.json().get("actions", []) if a.get("type") == "assign"]
    assert any(a.get("policy_ok") is False for a in assigns)


def test_routing_policy_and_autopilot(client: TestClient):
    org_id = "auto-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Auto"})
    put = client.put(
        f"/v1/orgs/{org_id}/mesh/routing-policy",
        headers=h,
        json={"auto_assign_from_queue": False, "suggest_on_call_on_drift": True},
    )
    assert put.status_code == 200
    getp = client.get(f"/v1/orgs/{org_id}/mesh/routing-policy", headers=h)
    assert getp.json()["routing_policy"].get("suggest_on_call_on_drift") is True
    run = client.post(f"/v1/orgs/{org_id}/mesh/autopilot/run?mode=dry_run", headers=h)
    assert run.status_code == 200
    assert run.json().get("mode") == "dry_run"


def test_intra_tenant_exchange(client: TestClient):
    tenant = "tenant-x"
    h = _h(client)
    for oid in ("src-org", "tgt-org"):
        client.post(
            "/v1/orgs",
            headers=h,
            json={"org_id": oid, "label": oid, "ugr_tenant_id": tenant},
        )
    pub = client.post(
        f"/v1/orgs/src-org/marketplace/listings",
        headers=h,
        json={
            "org_id": "src-org",
            "name": "handoff-listing",
            "visibility": "org",
            "steps": [{"subsystem": "lab", "kind": "lab.session"}],
        },
    )
    lid = pub.json()["listing_id"]
    if pub.json().get("approval_status") != "published":
        client.post(f"/v1/marketplace/listings/{lid}/approve", headers=h)
    xfer = client.post(
        f"/v1/tenants/{tenant}/exchange/listings/{lid}/transfer",
        headers=h,
        json={"source_org_id": "src-org", "target_org_id": "tgt-org"},
    )
    assert xfer.status_code == 200
    assert xfer.json()["listing"]["org_id"] == "tgt-org"


def test_peer_inbound_stub(tmp_path: Path):
    from platform.exchange.envelope import build_envelope

    svc = PlatformService(
        PlatformSettings(
            sqlite_path=tmp_path / "peer.sqlite3",
            audit_path=tmp_path / "audit.jsonl",
            runtime_root=tmp_path / "runtime",
            require_api_key=False,
            redis_url="",
        )
    )
    env = build_envelope(
        tenant_id="t1",
        source_org_id="a",
        target_org_id="b",
        kind="handoff.metadata",
        body={"note": "stub"},
        consent_by="admin",
        dual_consent=True,
    )
    assert verify_envelope(env)
    result = apply_inbound(store=svc.store, envelope=env)
    assert result.get("status") == "accepted"


def test_sovereign_profile_and_export_pack(client: TestClient):
    org_id = "sov-org"
    h = _h(client)
    client.post("/v1/orgs", headers=h, json={"org_id": org_id, "label": "Sov"})
    prof = client.put(
        f"/v1/orgs/{org_id}/sovereign/profile",
        headers=h,
        json={"mode": "self_hosted", "data_residency": "eu", "runner_endpoint": "https://runner.local"},
    )
    assert prof.status_code == 200
    assert prof.json()["sovereign_profile"]["mode"] == "self_hosted"
    pack = client.post(f"/v1/orgs/{org_id}/sovereign/export-pack", headers=h)
    assert pack.status_code == 200
    assert pack.headers.get("content-type", "").startswith("application/zip")


def test_exchange_peer_roundtrip(client: TestClient, tmp_path: Path, monkeypatch):
    from platform.api import create_app
    from platform.exchange.envelope import build_envelope
    from platform.service import PlatformService
    from platform.settings import PlatformSettings

    master = "test-master-key"
    settings_b = PlatformSettings(
        sqlite_path=tmp_path / "peer-b.sqlite3",
        audit_path=tmp_path / "audit-b.jsonl",
        runtime_root=tmp_path / "runtime-b",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        require_api_key=True,
        redis_url="",
    )
    svc_b = PlatformService(settings_b)
    app_b = create_app(service=svc_b, settings=settings_b)
    client_b = TestClient(app_b)

    def _fake_urlopen(req, timeout=10):
        resp = client_b.post(
            "/v1/exchange/inbound",
            content=req.data,
            headers={"Content-Type": "application/json", "X-Api-Key": master},
        )
        if resp.status_code >= 400:
            raise Exception(resp.text)

        class _Resp:
            status = resp.status_code

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return _Resp()

    monkeypatch.setattr("platform.exchange.peer.urllib.request.urlopen", _fake_urlopen)

    h = _h(client)
    client.post(
        "/v1/exchange/peers",
        headers=h,
        json={"peer_id": "peer-b", "base_url": "http://127.0.0.1:9999"},
    )
    env = build_envelope(
        tenant_id="t-peer",
        source_org_id="org-src",
        target_org_id="org-dst",
        kind="handoff.metadata",
        body={"note": "roundtrip"},
        consent_by="admin",
        dual_consent=True,
    )
    out = client.post(
        "/v1/exchange/outbound",
        headers=h,
        json={
            "peer_id": "peer-b",
            "tenant_id": "t-peer",
            "source_org_id": "org-src",
            "target_org_id": "org-dst",
            "kind": "handoff.metadata",
            "body": {"note": "roundtrip"},
            "dual_consent": True,
        },
    )
    assert out.status_code == 200
    assert out.json().get("status") == 200


def test_exchange_inbound_api(client: TestClient):
    from platform.exchange.envelope import build_envelope

    h = _h(client)
    env = build_envelope(
        tenant_id="t-in",
        source_org_id="org-a",
        target_org_id="org-b",
        kind="handoff.metadata",
        body={"k": "v"},
        consent_by="platform-admin",
        dual_consent=True,
    )
    resp = client.post("/v1/exchange/inbound", headers=h, json=env)
    assert resp.status_code == 200
    assert resp.json().get("status") == "accepted"
