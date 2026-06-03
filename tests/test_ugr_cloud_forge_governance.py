"""v3.0 governance — cloud_forge_profile_update via tenant_config target."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.governance_mission import run_governance_mission
from src.ugr.mission.mission_runtime import UGRMissionRuntime


class _GovRuntime:
    def __init__(self, runtime_dir: Path):
        self.runtime_dir = runtime_dir
        from src.ugr.mission.ingress import UrgIngressLaw
        from src.ugr.mission.mission_ledger import MissionLedger

        self.ingress_law = UrgIngressLaw()
        self.ledger = MissionLedger(runtime_dir=runtime_dir, tenant_id="tenant:acme")

    def _bind_tenant(self, tenant_id: str) -> None:
        from src.ugr.mission.mission_ledger import MissionLedger

        self.ledger = MissionLedger(runtime_dir=self.runtime_dir, tenant_id=tenant_id)


class TestCloudForgeProfileGovernance(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-cf-gov-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_GOVERNANCE_AUTHORITY_TOKEN"] = "gov-test-token"
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "cf-gov-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "cf-gov-urg"

    def tearDown(self):
        for key in (
            "AAIS_RUNTIME_DIR",
            "URG_GOVERNANCE_AUTHORITY_TOKEN",
            "URG_OPERATOR_RECEIPT_KEY",
            "URG_RECEIPT_SIGNING_KEY",
            "URG_GOVERNANCE_APPLY",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_profile_update_requires_governance_apply(self):
        runtime = _GovRuntime(self.temp_root)
        request = {
            "mission_kind": "governance_mutation",
            "mutation_target": "tenant_config",
            "mutation_op": "cloud_forge_profile_update",
            "operator_id": "operator-gov",
            "tenant_id": "tenant:acme",
            "aais_instance_id": "aais-primary",
            "governance_authority": "gov-test-token",
            "cloud_forge": {"latency_bias": 0.4, "wL_express_threshold": 110},
        }
        result = run_governance_mission(request, runtime=runtime)
        self.assertEqual(result["status"], "ok")
        tenants_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "tenants.json"
        payload = json.loads(tenants_path.read_text(encoding="utf-8"))
        acme_cf = dict(payload["tenants"]["tenant:acme"].get("cloud_forge") or {})
        self.assertNotEqual(float(acme_cf.get("latency_bias", 0)), 0.4)

    def test_profile_update_applies_when_enabled(self):
        os.environ["URG_GOVERNANCE_APPLY"] = "1"
        runtime = _GovRuntime(self.temp_root)
        request = {
            "mission_kind": "governance_mutation",
            "mutation_target": "tenant_config",
            "mutation_op": "cloud_forge_profile_update",
            "operator_id": "operator-gov",
            "tenant_id": "tenant:acme",
            "aais_instance_id": "aais-primary",
            "governance_authority": "gov-test-token",
            "cloud_forge": {
                "latency_bias": 0.42,
                "throughput_bias": 0.3,
                "intelligence_bias": 0.28,
                "wL_express_threshold": 99,
                "wL_express_floor": 44,
            },
        }
        result = run_governance_mission(request, runtime=runtime)
        self.assertEqual(result["status"], "ok")
        tenants_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "tenants.json"
        payload = json.loads(tenants_path.read_text(encoding="utf-8"))
        acme_cf = dict(payload["tenants"]["tenant:acme"].get("cloud_forge") or {})
        self.assertEqual(float(acme_cf["latency_bias"]), 0.42)
        self.assertEqual(float(acme_cf["wL_express_threshold"]), 99)
        acme_cf.update(
            {
                "latency_bias": 0.55,
                "throughput_bias": 0.3,
                "intelligence_bias": 0.15,
                "wL_express_threshold": 95,
                "wL_express_floor": 45,
            }
        )
        payload["tenants"]["tenant:acme"]["cloud_forge"] = acme_cf
        tenants_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
