"""Full-stack Infinity Pilot smoke (Platform + UGR bridge + boundaries)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from platform.api import create_app
from platform.auth.api_keys import hash_api_key
from platform.ledger.writer import verify_ledger_chain
from platform.service import PlatformService
from platform.settings import PlatformSettings


class TestInfinityPilotStackSmoke(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="pilot-stack-"))
        master = "pilot-stack-key"
        self.settings = PlatformSettings(
            sqlite_path=self.tmp / "platform.sqlite3",
            audit_path=self.tmp / "audit.jsonl",
            runtime_root=self.tmp / "runtime",
            master_api_key=master,
            master_api_key_hash=hash_api_key(master),
            require_api_key=True,
            redis_url="",
        )
        self.svc = PlatformService(self.settings)
        self.app = create_app(service=self.svc, settings=self.settings)
        self.client = TestClient(self.app)
        self.headers = {"X-Api-Key": master}

    def test_platform_org_ledger_and_witness_off_by_default(self):
        org_id = "pilot-stack-org"
        r = self.client.post("/v1/orgs", headers=self.headers, json={"org_id": org_id, "label": "Pilot"})
        self.assertEqual(r.status_code, 200)
        job = self.client.post(
            "/v1/jobs",
            headers=self.headers,
            json={"org_id": org_id, "subsystem": "lab", "kind": "lab.session"},
        )
        self.assertEqual(job.status_code, 200)
        verify = self.client.get(f"/v1/orgs/{org_id}/ledger/verify", headers=self.headers)
        self.assertTrue(verify.json().get("valid"))
        overlay = self.client.get(f"/v1/orgs/{org_id}/ledger/cognition-overlay?limit=5", headers=self.headers)
        self.assertEqual(overlay.status_code, 200)
        self.assertTrue(overlay.json().get("read_only"))

    def test_ugr_bridge_integrated_with_trust_organ(self):
        from src.ugr.ledger_bridge.bridge import LedgerBridge, LedgerClaim

        class _FakeOrgan:
            def receive_claim(self, claim, *, bridge_trace=None):
                return {"acknowledged": True, "receipt_id": "r1", "claim_id": claim.get("claim_id")}

        bridge = LedgerBridge(trust_organ=_FakeOrgan(), trace_path=self.tmp / "trace.jsonl")
        result = bridge.traverse(
            LedgerClaim(
                claim_id="stack-claim",
                law_id="law-1",
                law_version="1.0",
                sigil="s1",
                source_node="n1",
            ),
            session_id="sess",
            law_id="law-1",
            law_version="1.0",
        )
        self.assertEqual(result.claim_label, "proven")

    def test_ledger_chain_local(self):
        from platform.ledger.writer import append_ledger_entry

        org_id = "pilot-ledger-org"
        self.client.post("/v1/orgs", headers=self.headers, json={"org_id": org_id, "label": "L"})
        append_ledger_entry(
            store=self.svc.store,
            org_id=org_id,
            kind="pilot.smoke",
            payload={"ok": True},
        )
        ok, _ = verify_ledger_chain(store=self.svc.store, org_id=org_id)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
