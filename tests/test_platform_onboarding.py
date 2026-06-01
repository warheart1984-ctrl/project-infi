"""Onboarding invite → job → list flow."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.service import PlatformService
from platform.settings import PlatformSettings


def test_onboarding_mechanic_job(tmp_path: Path) -> None:
    master = "test-master-key"
    settings = PlatformSettings(
        sqlite_path=tmp_path / "ob.sqlite3",
        audit_path=tmp_path / "audit.jsonl",
        runtime_root=tmp_path / "rt",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        redis_url="",
    )
    client = TestClient(create_app(service=PlatformService(settings), settings=settings))
    mh = {"X-Api-Key": master}
    client.post("/v1/orgs", headers=mh, json={"org_id": "onboard-co"})
    inv = client.post("/v1/orgs/onboard-co/invites", headers=mh, json={"email": "u@x.com", "role": "operator"})
    acc = client.post(
        "/v1/invites/accept",
        json={"token": inv.json()["invite_token"], "principal_id": "u1", "display_name": "User"},
    )
    key = acc.json()["api_key"]
    job = client.post(
        "/v1/jobs",
        headers={"X-Api-Key": key},
        json={
            "subsystem": "mechanic",
            "kind": "mechanic.scan",
            "params": {"case_id": "onboard-j1", "repo_path": "mechanic/fixtures/sample-customer-repo"},
        },
    )
    assert job.status_code == 200
    listed = client.get("/v1/jobs?org_id=onboard-co", headers={"X-Api-Key": key})
    assert any(j["job_id"] == job.json()["job_id"] for j in listed.json()["jobs"])
