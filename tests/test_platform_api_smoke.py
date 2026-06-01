"""Platform API smoke tests (sqlite, inline worker)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.service import PlatformService
from platform.settings import PlatformSettings


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    db = tmp_path / "platform.sqlite3"
    audit = tmp_path / "audit.jsonl"
    master = "test-master-key"
    settings = PlatformSettings(
        sqlite_path=db,
        audit_path=audit,
        runtime_root=tmp_path / "runtime",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        require_api_key=True,
        redis_url="",
    )
    svc = PlatformService(settings)
    app = create_app(service=svc, settings=settings)
    return TestClient(app)


def test_health_no_auth(client: TestClient) -> None:
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "platform-membrane"


def test_org_job_artifact_flow(client: TestClient) -> None:
    headers = {"X-Api-Key": "test-master-key"}
    org = client.post(
        "/v1/orgs",
        headers=headers,
        json={"org_id": "smoke-org", "label": "Smoke Org"},
    )
    assert org.status_code == 200

    key_resp = client.post(
        "/v1/orgs/smoke-org/api-keys",
        headers=headers,
        json={"principal_id": "op-1", "roles": ["operator"]},
    )
    assert key_resp.status_code == 200
    op_key = key_resp.json()["api_key"]
    op_headers = {"X-Api-Key": op_key}

    job = client.post(
        "/v1/jobs",
        headers=op_headers,
        json={
            "subsystem": "mechanic",
            "kind": "mechanic.scan",
            "params": {
                "case_id": "platform-smoke-case",
                "repo_path": "mechanic/fixtures/sample-customer-repo",
            },
        },
    )
    assert job.status_code == 200
    job_id = job.json()["job_id"]
    assert job.json()["status"] in {"complete", "queued", "running", "failed"}

    detail = client.get(f"/v1/jobs/{job_id}", headers=op_headers)
    assert detail.status_code == 200

    artifacts = client.get(
        "/v1/artifacts",
        headers=op_headers,
        params={"org_id": "smoke-org", "subsystem": "mechanic"},
    )
    assert artifacts.status_code == 200

    audit = client.get("/v1/audit", headers=headers, params={"org_id": "smoke-org"})
    assert audit.status_code == 200
