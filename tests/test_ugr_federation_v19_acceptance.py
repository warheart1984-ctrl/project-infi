"""v1.9 acceptance — cross-tenant governance dual ledger + trust witness (no mocks)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.federation_grants import (
    CAP_GOVERNANCE_COSIGN,
    CAP_ROUTE_STEP,
    FederationGrantStore,
)
from src.ugr.mission.mission_runtime import UGRMissionRuntime
from src.ugr.trust_bundle.organ import TrustBundleOrgan
from src.ugr.trust_bundle.scenarios import scenario_federation_dual_ledger


class TestFederationV19Acceptance(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-fed-v19-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "fed-v19-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "fed-v19-urg"
        os.environ["URG_GOVERNANCE_APPLY"] = "1"
        os.environ["URG_GOVERNANCE_OPERATOR_ALLOWLIST"] = "operator-acme"

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        os.environ.pop("URG_GOVERNANCE_APPLY", None)
        os.environ.pop("URG_GOVERNANCE_OPERATOR_ALLOWLIST", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_v19_cross_tenant_governance_dual_ledger_and_witness(self):
        store = FederationGrantStore(self.temp_root)
        grant = store.issue(
            issuer_tenant="tenant:acme",
            grantee_tenant="tenant:contoso",
            capabilities=[CAP_ROUTE_STEP, CAP_GOVERNANCE_COSIGN],
            operator_id="operator-acme",
        )
        store.accept(
            grant.grant_id,
            accepting_tenant="tenant:contoso",
            operator_id="operator-contoso",
        )

        organ_id = "organ-fed-test-v19"
        gov_payload = {
            "operator_id": "operator-acme",
            "tenant_id": "tenant:acme",
            "aais_instance_id": "aais-local-1",
            "mission_kind": "governance_mutation",
            "mutation_target": "provider_organs",
            "mutation_op": "federation_organ_admit",
            "federation_peer_tenant": "tenant:contoso",
            "federation_grant_id": grant.grant_id,
            "organ_id": organ_id,
            "organ_spec": {
                "organ_id": organ_id,
                "identity": {"label": "Federation test organ", "tier": "tiny"},
                "envelope": {"execution_backend": "local", "proposal_only": True},
                "function": {"capabilities": ["text"], "max_tokens": 64},
                "contract": {
                    "risk_ceiling": "low",
                    "allowed_regions": ["tenant-us", "tenant-eu"],
                    "admissible_rails": ["SAFE", "NORMAL"],
                },
            },
        }
        runtime = UGRMissionRuntime(runtime_dir=self.temp_root)
        gov_result = runtime.run_mission(gov_payload)
        self.assertEqual(gov_result["status"], "ok", gov_result.get("summary"))

        mission_id = gov_result["mission_id"]
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
        acme_text = acme_ledger.read_text(encoding="utf-8")
        contoso_text = contoso_ledger.read_text(encoding="utf-8")
        self.assertIn("federation_governance", acme_text)
        self.assertIn("federation_governance_inbound", contoso_text)
        self.assertIn(mission_id, contoso_text)

        witness_root = self.temp_root / "witness"
        witness_root.mkdir(parents=True, exist_ok=True)
        evidence = scenario_federation_dual_ledger(
            machine_id="machine-a",
            runtime_root=witness_root,
        )
        self.assertEqual(evidence.status, "pass", evidence.details)

        organ = TrustBundleOrgan(
            output_dir=self.temp_root / "trust-bundles" / "latest",
            scenarios=("federation_dual_ledger",),
            machine_ids=("machine-a",),
        )
        bundle = organ.run()
        fed_records = [
            r
            for r in bundle.get("scenario_records", [])
            if r.get("scenario_id") == "federation_dual_ledger"
        ]
        self.assertTrue(fed_records)
        self.assertEqual(fed_records[0].get("status"), "pass")
        self.assertEqual(bundle.get("overall_status"), "pass")


if __name__ == "__main__":
    unittest.main()
