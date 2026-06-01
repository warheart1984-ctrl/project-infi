"""Job graph endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.service import PlatformService
from platform.settings import PlatformSettings


def test_job_graph_returns_nodes(tmp_path: Path) -> None:
    master = "test-master-key"
    settings = PlatformSettings(
        sqlite_path=tmp_path / "g.sqlite3",
        audit_path=tmp_path / "audit.jsonl",
        runtime_root=tmp_path / "rt",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        redis_url="",
    )
    client = TestClient(create_app(service=PlatformService(settings), settings=settings))
    h = {"X-Api-Key": master}
    client.post("/v1/orgs", headers=h, json={"org_id": "g-org"})
    job = client.post(
        "/v1/jobs",
        headers=h,
        json={
            "org_id": "g-org",
            "subsystem": "mechanic",
            "kind": "mechanic.scan",
            "params": {"case_id": "g-case", "repo_path": "mechanic/fixtures/sample-customer-repo"},
        },
    ).json()
    graph = client.get(f"/v1/jobs/{job['job_id']}/graph?org_id=g-org", headers=h)
    assert graph.status_code == 200
    assert len(graph.json().get("nodes") or []) >= 1
