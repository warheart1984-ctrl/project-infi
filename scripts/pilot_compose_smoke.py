#!/usr/bin/env python3
"""Smoke test for Infinity Pilot Platform API (local TestClient or live compose)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def smoke_http(*, base_url: str, api_key: str) -> int:
    base = base_url.rstrip("/")
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}

    def get(path: str) -> dict:
        req = urllib.request.Request(f"{base}{path}", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def post(path: str, body: dict) -> dict:
        data = json.dumps(body).encode()
        req = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    get("/v1/health")
    org_id = "pilot-smoke-org"
    post("/v1/orgs", {"org_id": org_id, "label": "Pilot Smoke"})
    post("/v1/jobs", {"org_id": org_id, "subsystem": "lab", "kind": "lab.session"})
    verify = get(f"/v1/orgs/{org_id}/ledger/verify")
    if not verify.get("valid"):
        raise RuntimeError(f"ledger verify failed: {verify}")
    overlay = get(f"/v1/orgs/{org_id}/ledger/cognition-overlay?limit=5")
    if not overlay.get("read_only"):
        raise RuntimeError("cognition overlay not read_only")
    print("OK: pilot compose smoke")
    return 0


def smoke_local() -> int:
    import importlib
    import sys
    from pathlib import Path
    import tempfile

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if "platform" in sys.modules and not hasattr(sys.modules["platform"], "__path__"):
        del sys.modules["platform"]

    from fastapi.testclient import TestClient

    create_app = importlib.import_module("platform.api").create_app
    hash_api_key = importlib.import_module("platform.auth.api_keys").hash_api_key
    PlatformService = importlib.import_module("platform.service").PlatformService
    PlatformSettings = importlib.import_module("platform.settings").PlatformSettings

    master = "pilot-local-smoke"
    tmp = Path(tempfile.mkdtemp(prefix="pilot-smoke-"))
    settings = PlatformSettings(
        sqlite_path=tmp / "p.sqlite3",
        audit_path=tmp / "audit.jsonl",
        runtime_root=tmp / "runtime",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        require_api_key=True,
        redis_url="",
    )
    client = TestClient(create_app(service=PlatformService(settings), settings=settings))
    h = {"X-Api-Key": master}
    assert client.get("/v1/health", headers=h).status_code == 200
    client.post("/v1/orgs", headers=h, json={"org_id": "local-smoke", "label": "L"})
    client.post("/v1/jobs", headers=h, json={"org_id": "local-smoke", "subsystem": "lab", "kind": "lab.session"})
    assert client.get("/v1/orgs/local-smoke/ledger/verify", headers=h).json().get("valid")
    print("OK: pilot local smoke")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:8090")
    parser.add_argument("--api-key", default="change-me-pilot-master")
    args = parser.parse_args()
    try:
        if args.local:
            return smoke_local()
        return smoke_http(base_url=args.base_url, api_key=args.api_key)
    except (urllib.error.URLError, RuntimeError, AssertionError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
