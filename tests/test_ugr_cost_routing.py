"""Tests for URG cost-aware routing (Phase 2)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.cost_routing import MissionBudget, resolve_mission_budget
from src.ugr.mission.mission_receipt import FAILURE_REASON_BUDGET_EXCEEDED, map_failure_reason
from src.ugr.mission.mission_runtime import UGRMissionRuntime
from src.ugr.mission.organ_matcher import resolve_step_organ
from src.ugr.mission.provider_organ import ProviderOrganRegistry


class TestCostRouting(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-cost-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "cost-test-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "cost-test-urg"
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo-auto.json"
        self.demo_auto = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]
        self.demo_auto["tenant_id"] = "tenant:acme"

    def tearDown(self):
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_mission_budget_resolves_hard_ceil(self):
        budget = resolve_mission_budget(
            {"constraints": {"mission_budget": {"soft_ceil": 10, "hard_ceil": 12, "per_step_max": 8}}}
        )
        self.assertEqual(budget.hard_ceil, 12.0)
        self.assertEqual(budget.soft_ceil, 10.0)

    def test_auto_assign_picks_cheapest_in_tier(self):
        registry = ProviderOrganRegistry(tenant_id="tenant:acme")
        organ, meta = resolve_step_organ(
            {"tier": "tiny"},
            ordinal=1,
            step_count=1,
            organ_registry=registry,
            region_id="tenant-us",
            intent="governed_super_router_demo",
            constraints={"mission_budget": {"hard_ceil": 25, "soft_ceil": 20}},
        )
        self.assertIsNotNone(organ)
        self.assertEqual(organ.organ_id, "organ-local-tiny")
        self.assertIn("cost_ranked", meta.get("match_reason", ""))

    def test_hard_budget_blocks_mission(self):
        payload = {
            "operator_id": "cost-op",
            "tenant_id": "tenant:acme",
            "aais_instance_id": "aais-primary",
            "region_id": "tenant-us",
            "intent": "governed_super_router_demo",
            "aais_step_bridge": False,
            "constraints": {
                "mission_budget": {"soft_ceil": 1, "hard_ceil": 1, "per_step_max": 2},
                "risk_ceiling": "low",
            },
            "steps": [
                {"step_id": "s1", "objective": "tiny", "organ_id": "organ-local-tiny"},
                {"step_id": "s2", "objective": "mid", "organ_id": "organ-openrouter-mid"},
            ],
        }
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(payload)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(
            "budget" in str(result.get("summary") or "").lower()
            or (result.get("mission_receipt_schema") or {}).get("failure_reason")
            == FAILURE_REASON_BUDGET_EXCEEDED
        )
        schema = result.get("mission_receipt_schema") or {}
        if schema.get("failure_reason"):
            self.assertEqual(schema["failure_reason"], FAILURE_REASON_BUDGET_EXCEEDED)
