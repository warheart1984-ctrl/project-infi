"""v1.8 acceptance — paired receipt federation_digest + counterparty resolve (no mocks)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.federation_grants import CAP_ROUTE_STEP, FederationGrantStore, compute_federation_digest
from src.ugr.mission.mission_ledger import MissionLedger
from src.ugr.mission.mission_receipt_store import MissionReceiptStore
from src.ugr.mission.mission_runtime import UGRMissionRuntime


class TestFederationV18Acceptance(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-fed-v18-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "fed-v18-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "fed-v18-urg"
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

    def _run_bilateral_mission(self) -> tuple[dict, str]:
        store = FederationGrantStore(self.temp_root)
        grant = store.issue(
            issuer_tenant="tenant:acme",
            grantee_tenant="tenant:contoso",
            capabilities=[CAP_ROUTE_STEP],
            operator_id="operator-acme",
        )
        store.accept(
            grant.grant_id,
            accepting_tenant="tenant:contoso",
            operator_id="operator-contoso",
        )
        mission = json.loads(json.dumps(self.demo_template))
        for step in mission["steps"]:
            if step.get("federation_grant_id") == "__GRANT_ID__":
                step["federation_grant_id"] = grant.grant_id
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(mission)
        return result, grant.grant_id

    def test_v18_paired_receipt_resolves_counterparty(self):
        result, grant_id = self._run_bilateral_mission()
        self.assertEqual(result["status"], "ok")
        mission_id = result["mission_id"]
        schema = dict(result.get("mission_receipt_schema") or {})
        self.assertIn("federation_digest", schema)
        self.assertIn("counterparty_receipt_ref", schema)

        home_store = MissionReceiptStore(runtime_dir=self.temp_root, tenant_id="tenant:acme")
        record = home_store.get_receipt(mission_id, tenant_id="tenant:acme")
        self.assertIsNotNone(record)
        stored_schema = dict(record.get("mission_receipt_schema") or {})
        self.assertEqual(
            stored_schema.get("federation_digest"),
            schema.get("federation_digest"),
        )

        home_ledger = MissionLedger(runtime_dir=self.temp_root, tenant_id="tenant:acme")
        peer_ledger = MissionLedger(runtime_dir=self.temp_root, tenant_id="tenant:contoso")
        expected_digest = compute_federation_digest(
            home_rows=home_ledger.list_for_mission(mission_id),
            peer_rows=peer_ledger.list_for_mission(mission_id),
            grant_id=grant_id,
        )
        self.assertEqual(schema["federation_digest"], expected_digest)

        peer_store = MissionReceiptStore(runtime_dir=self.temp_root, tenant_id="tenant:contoso")
        resolved = peer_store.resolve_counterparty_ref(
            dict(schema.get("counterparty_receipt_ref") or {})
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.get("kind"), "federation_counterparty_stub")
        self.assertEqual(resolved.get("home_mission_id"), mission_id)


if __name__ == "__main__":
    unittest.main()
