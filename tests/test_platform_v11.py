"""Platform v1.1 RBAC, scopes, and cross-org tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.auth.rbac import authorize_scope, principal_from_resolution
from platform.service import PlatformService
from platform.settings import PlatformSettings


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    master = "test-master-key"
    settings = PlatformSettings(
        sqlite_path=tmp_path / "p.sqlite3",
        audit_path=tmp_path / "audit.jsonl",
        runtime_root=tmp_path / "rt",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        require_api_key=True,
        redis_url="",
    )
    svc = PlatformService(settings)
    return TestClient(create_app(service=svc, settings=settings))


def test_scoped_key_cannot_create_job_without_scope(client: TestClient) -> None:
    headers = {"X-Api-Key": "test-master-key"}
    client.post("/v1/orgs", headers=headers, json={"org_id": "acme", "label": "Acme"})
    key_resp = client.post(
        "/v1/orgs/acme/api-keys",
        headers=headers,
        json={
            "principal_id": "viewer-1",
            "roles": ["read_only"],
            "scopes": ["jobs:read"],
        },
    )
    read_key = key_resp.json()["api_key"]
    job = client.post(
        "/v1/jobs",
        headers={"X-Api-Key": read_key},
        json={"subsystem": "mechanic", "kind": "mechanic.scan", "params": {"case_id": "x"}},
    )
    assert job.status_code == 403


def test_cross_org_job_hidden(client: TestClient) -> None:
    master = {"X-Api-Key": "test-master-key"}
    client.post("/v1/orgs", headers=master, json={"org_id": "org-a"})
    client.post("/v1/orgs", headers=master, json={"org_id": "org-b"})
    ka = client.post(
        "/v1/orgs/org-a/api-keys",
        headers=master,
        json={"principal_id": "a-op", "roles": ["operator"]},
    ).json()["api_key"]
    job = client.post(
        "/v1/jobs",
        headers={"X-Api-Key": ka},
        json={
            "subsystem": "mechanic",
            "kind": "mechanic.scan",
            "params": {"case_id": "secret-a", "repo_path": "mechanic/fixtures/sample-customer-repo"},
        },
    ).json()
    kb = client.post(
        "/v1/orgs/org-b/api-keys",
        headers=master,
        json={"principal_id": "b-op", "roles": ["operator"]},
    ).json()["api_key"]
    peek = client.get(f"/v1/jobs/{job['job_id']}", headers={"X-Api-Key": kb})
    assert peek.status_code == 404


def test_invite_accept_flow(client: TestClient) -> None:
    master = {"X-Api-Key": "test-master-key"}
    client.post("/v1/orgs", headers=master, json={"org_id": "invite-org"})
    inv = client.post(
        "/v1/orgs/invite-org/invites",
        headers=master,
        json={"email": "f@ex.com", "role": "operator"},
    )
    assert inv.status_code == 200
    token = inv.json()["invite_token"]
    acc = client.post(
        "/v1/invites/accept",
        json={"token": token, "principal_id": "friend-1", "display_name": "Friend"},
    )
    assert acc.status_code == 200
    assert acc.json().get("api_key")


def test_authorize_scope_helper() -> None:
    p = principal_from_resolution(
        {
            "principal_id": "p1",
            "org_id": "o1",
            "roles": ["operator"],
            "scopes": ["jobs:submit", "jobs:read"],
        }
    )
    assert authorize_scope(principal=p, scope="jobs:submit")
    assert not authorize_scope(principal=p, scope="org:billing")
