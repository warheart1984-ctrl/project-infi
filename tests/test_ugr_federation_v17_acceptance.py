"""v1.7 acceptance — bilateral grant + federated step dual ledger (no mocks)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.federation_grants import (
    CAP_ROUTE_STEP,
    FederationGrantStore,
    GRANT_STATUS_ACCEPTED,
)
from src.ugr.mission.mission_runtime import UGRMissionRuntime


class TestFederationV17Acceptance(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-fed-v17-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "fed-v17-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "fed-v17-urg"
        demo_path = (
            Path(__file__).resolve().parents[1]
            / "deploy"
            / "ugr"
            / "mission-demo-federation-v17.json"
        )
        self.demo_template = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_v17_bilateral_grant_federated_step_dual_ledger(self):
        store = FederationGrantStore(self.temp_root)
        grant = store.issue(
            issuer_tenant="tenant:acme",
            grantee_tenant="tenant:contoso",
            capabilities=[CAP_ROUTE_STEP],
            operator_id="operator-acme",
        )
        accepted = store.accept(
            grant.grant_id,
            accepting_tenant="tenant:contoso",
            operator_id="operator-contoso",
        )
        self.assertEqual(accepted.status, GRANT_STATUS_ACCEPTED)

        mission = json.loads(json.dumps(self.demo_template))
        for step in mission["steps"]:
            if step.get("federation_grant_id") == "__GRANT_ID__":
                step["federation_grant_id"] = grant.grant_id

        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(mission)
        self.assertEqual(result["status"], "ok", result.get("summary"))

        grants_path = self.temp_root / "urg" / "federation" / "grants.jsonl"
        self.assertTrue(grants_path.exists())
        grant_lines = grants_path.read_text(encoding="utf-8")
        self.assertIn(GRANT_STATUS_ACCEPTED, grant_lines)
        self.assertIn(grant.grant_id, grant_lines)

        mission_id = result["mission_id"]
        acme_ledger = (
            self.temp_root
            / "collective-pattern-ledger"
            / "tenants"
            / "tenant-acme"
            / "missions.jsonl"
        )
        contoso_ledger = (
            self.temp_root
            / "collective-pattern-ledger"
            / "tenants"
            / "tenant-contoso"
            / "missions.jsonl"
        )
        self.assertTrue(acme_ledger.exists())
        self.assertTrue(contoso_ledger.exists())

        acme_rows = [
            json.loads(line)
            for line in acme_ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        contoso_rows = [
            json.loads(line)
            for line in contoso_ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        fed_home = [
            r
            for r in acme_rows
            if r.get("phase") == "federation_step" and r.get("mission_id") == mission_id
        ]
        fed_inbound = [
            r
            for r in contoso_rows
            if r.get("phase") == "federation_inbound" and r.get("home_mission_id") == mission_id
        ]
        self.assertTrue(fed_home, "acme ledger must record federation_step")
        self.assertTrue(fed_inbound, "contoso ledger must record federation_inbound")
        self.assertEqual(fed_home[0].get("federation_grant_id"), grant.grant_id)
        self.assertEqual(fed_inbound[0].get("grant_id"), grant.grant_id)

    def test_v17_pending_grant_blocks_federated_step(self):
        store = FederationGrantStore(self.temp_root)
        grant = store.issue(
            issuer_tenant="tenant:acme",
            grantee_tenant="tenant:contoso",
            capabilities=[CAP_ROUTE_STEP],
            operator_id="operator-acme",
        )
        mission = json.loads(json.dumps(self.demo_template))
        for step in mission["steps"]:
            if step.get("federation_grant_id") == "__GRANT_ID__":
                step["federation_grant_id"] = grant.grant_id

        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(mission)
        self.assertIn(result["status"], {"blocked", "rejected"})
        contoso_ledger = (
            self.temp_root
            / "collective-pattern-ledger"
            / "tenants"
            / "tenant-contoso"
            / "missions.jsonl"
        )
        if contoso_ledger.exists():
            text = contoso_ledger.read_text(encoding="utf-8")
            self.assertNotIn("federation_inbound", text)


if __name__ == "__main__":
    unittest.main()
