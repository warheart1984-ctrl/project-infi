"""v2.0 acceptance — URG tenant spec binds to Cloud Forge PerformanceProfile."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.cloud_forge_bridge import (
    build_forge_profile_from_tenant,
    schedule_rail_for_ugr,
)
from src.ugr.mission.mission_runtime import UGRMissionRuntime
from src.ugr.platform.tenant_registry import TenantRegistry


class TestCloudForgeTenantBinding(unittest.TestCase):
    def test_derived_express_thresholds_from_cost_ceiling(self):
        acme = build_forge_profile_from_tenant("tenant:acme")
        contoso = build_forge_profile_from_tenant("tenant:contoso")
        self.assertGreater(
            float(contoso["wL_express_threshold"]),
            float(acme["wL_express_threshold"]),
        )
        self.assertGreater(
            float(contoso["wL_express_floor"]),
            float(acme["wL_express_floor"]),
        )

    def test_explicit_tenant_profiles_differ(self):
        acme = build_forge_profile_from_tenant("tenant:acme")
        contoso = build_forge_profile_from_tenant("tenant:contoso")
        self.assertNotEqual(acme["latency_bias"], contoso["latency_bias"])
        self.assertNotEqual(acme["wL_express_threshold"], contoso["wL_express_threshold"])

    def test_schedule_rail_differs_by_tenant(self):
        acme_bundle = schedule_rail_for_ugr(
            {
                "question": "same objective for rail comparison",
                "intent": "governed_super_router_demo",
                "tenant_id": "tenant:acme",
                "context": {"forbid_express": False},
            },
            trace_id="forge-acme",
        )
        contoso_bundle = schedule_rail_for_ugr(
            {
                "question": "same objective for rail comparison",
                "intent": "governed_super_router_demo",
                "tenant_id": "tenant:contoso",
                "context": {"forbid_express": False},
            },
            trace_id="forge-contoso",
        )
        self.assertIsNotNone(acme_bundle)
        self.assertIsNotNone(contoso_bundle)
        acme_plan = dict(acme_bundle.get("cognition_plan") or {})
        contoso_plan = dict(contoso_bundle.get("cognition_plan") or {})
        acme_tier = acme_plan.get("model_tier")
        contoso_tier = contoso_plan.get("model_tier")
        if acme_tier and contoso_tier:
            self.assertNotEqual(acme_tier, contoso_tier)


class TestMissionCloudForgeTenantDigest(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-cf-bind-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "cf-bind-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "cf-bind-urg"
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json"
        self.demo = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_mission_ingress_has_cloud_forge_tenant_digest(self):
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(self.demo)
        self.assertEqual(result["status"], "ok")
        ingress = result.get("urg_ingress") or {}
        self.assertTrue(ingress.get("cloud_forge_tenant_digest"))
        self.assertEqual(ingress.get("cloud_forge_binding_version"), "3.0")


if __name__ == "__main__":
    unittest.main()
