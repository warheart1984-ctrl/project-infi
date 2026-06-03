"""v2.1 acceptance — federated step uses peer tenant Cloud Forge rail."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.federation_grants import CAP_ROUTE_STEP, FederationGrantStore
from src.ugr.mission.mission_runtime import UGRMissionRuntime


class TestFederationForgePeerRail(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-fed-forge-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "fed-forge-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "fed-forge-urg"
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

    def test_federated_step_has_peer_cloud_forge_bundle(self):
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
        self.assertEqual(result["status"], "ok", result.get("summary"))

        home_cf = dict(result.get("cloud_forge") or {})
        home_rail = str((home_cf.get("rail_decision") or {}).get("rail") or "")

        federated_steps = [
            s
            for s in result.get("steps") or []
            if s.get("federation_peer_tenant") == "tenant:contoso"
        ]
        self.assertEqual(len(federated_steps), 1)
        peer_cf = dict(federated_steps[0].get("cloud_forge") or {})
        self.assertTrue(peer_cf.get("rail_decision"))
        peer_rail = str((peer_cf.get("rail_decision") or {}).get("rail") or "")
        self.assertTrue(peer_rail)

        schema = dict(result.get("mission_receipt_schema") or {})
        self.assertIn("federation_digest", schema)

        ingress = result.get("urg_ingress") or {}
        fed_ctx = list(ingress.get("federation_context") or [])
        self.assertTrue(fed_ctx)
        self.assertEqual(fed_ctx[0].get("mission_rail"), home_rail)
        self.assertEqual(fed_ctx[0].get("peer_rail"), peer_rail)

    def test_federated_mission_ok_with_divergent_rails_when_boundary_extended(self):
        store = FederationGrantStore(self.temp_root)
        grant = store.issue(
            issuer_tenant="tenant:acme",
            grantee_tenant="tenant:contoso",
            capabilities=[CAP_ROUTE_STEP, "forge_peer_rail"],
            operator_id="operator-acme",
        )
        store.accept(
            grant.grant_id,
            accepting_tenant="tenant:contoso",
            operator_id="operator-contoso",
        )
        mission = json.loads(json.dumps(self.demo_template))
        mission["context"] = {"forbid_express": False}
        for step in mission["steps"]:
            if step.get("federation_grant_id") == "__GRANT_ID__":
                step["federation_grant_id"] = grant.grant_id

        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(mission)
        self.assertEqual(result["status"], "ok", result.get("summary"))
        schema = dict(result.get("mission_receipt_schema") or {})
        self.assertEqual(schema.get("schema_version"), "1.4")
        if schema.get("federation_forge_digest"):
            self.assertTrue(len(schema["federation_forge_digest"]) == 64)

        from src.ugr.mission.mission_ledger import MissionLedger

        mission_id = result["mission_id"]
        rows = MissionLedger(
            runtime_dir=self.temp_root, tenant_id="tenant:acme"
        ).list_for_mission(mission_id)
        fed_ctx = list((result.get("urg_ingress") or {}).get("federation_context") or [])
        home_rail = fed_ctx[0].get("mission_rail") if fed_ctx else ""
        peer_rail = fed_ctx[0].get("peer_rail") if fed_ctx else ""
        if home_rail != peer_rail:
            extend_rows = [r for r in rows if r.get("phase") == "federation_boundary_extend"]
            self.assertGreaterEqual(len(extend_rows), 1)


if __name__ == "__main__":
    unittest.main()
