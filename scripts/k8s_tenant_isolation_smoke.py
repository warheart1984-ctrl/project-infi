#!/usr/bin/env python3
"""Platform API tenant isolation smoke — logical cross-tenant boundary proof."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def run_smoke(*, emit_report: bool = True) -> dict:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from fastapi.testclient import TestClient
    from platform.api import create_app
    from platform.auth.api_keys import hash_api_key
    from platform.ledger.writer import append_ledger_entry
    from platform.service import PlatformService
    from platform.settings import PlatformSettings

    master = "k8s-isolation-smoke-key"
    tmp = Path(tempfile.mkdtemp(prefix="k8s-iso-"))
    settings = PlatformSettings(
        sqlite_path=tmp / "platform.sqlite3",
        audit_path=tmp / "audit.jsonl",
        runtime_root=tmp / "runtime",
        master_api_key=master,
        master_api_key_hash=hash_api_key(master),
        require_api_key=True,
        redis_url="",
    )
    svc = PlatformService(settings)
    client = TestClient(create_app(service=svc, settings=settings))
    headers = {"X-Api-Key": master}

    org_a = "tenant-a-org"
    org_b = "tenant-b-org"
    client.post("/v1/orgs", headers=headers, json={"org_id": org_a, "label": "A", "ugr_tenant_id": "tenant:acme"})
    client.post("/v1/orgs", headers=headers, json={"org_id": org_b, "label": "B", "ugr_tenant_id": "tenant:contoso"})
    append_ledger_entry(store=svc.store, org_id=org_a, kind="iso.smoke", payload={"secret": "a-only"})
    append_ledger_entry(store=svc.store, org_id=org_b, kind="iso.smoke", payload={"secret": "b-only"})

    verify_a = client.get(f"/v1/orgs/{org_a}/ledger/verify", headers=headers).json()
    verify_b = client.get(f"/v1/orgs/{org_b}/ledger/verify", headers=headers).json()

    overlay_a = client.get(f"/v1/orgs/{org_a}/ledger/cognition-overlay?limit=20", headers=headers).json()
    overlay_b = client.get(f"/v1/orgs/{org_b}/ledger/cognition-overlay?limit=20", headers=headers).json()
    a_text = json.dumps(overlay_a)
    b_text = json.dumps(overlay_b)
    cross_blocked = "b-only" not in a_text and "a-only" not in b_text

    entries_a = svc.store.list_ledger_entries(org_id=org_a, limit=20)
    entries_b = svc.store.list_ledger_entries(org_id=org_b, limit=20)
    partition_ok = any("a-only" in json.dumps(e) for e in entries_a)
    partition_ok = partition_ok and any("b-only" in json.dumps(e) for e in entries_b)
    partition_ok = partition_ok and not any("a-only" in json.dumps(e) for e in entries_b)
    partition_ok = partition_ok and not any("b-only" in json.dumps(e) for e in entries_a)

    report = {
        "status": "pass"
        if verify_a.get("valid") and verify_b.get("valid") and cross_blocked and partition_ok
        else "fail",
        "org_a_verify": verify_a.get("valid"),
        "org_b_verify": verify_b.get("valid"),
        "cross_tenant_blocked": cross_blocked,
        "ledger_partition_ok": partition_ok,
        "tenant_a": "tenant:acme",
        "tenant_b": "tenant:contoso",
    }

    if emit_report:
        out = root / "ci-artifacts" / "k8s_isolation_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="K8s tenant isolation smoke (logical Platform API)")
    parser.parse_args()
    report = run_smoke()
    print(json.dumps(report, indent=2))
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
