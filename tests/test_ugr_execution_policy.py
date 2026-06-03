"""Tests for URG execution modes, kill switch, and execution_committed lifecycle."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ugr.invariants.execution_safety import check_execution_safety
from src.ugr.mission.execution_policy import (
    EXECUTION_MODE_DRY_RUN,
    EXECUTION_MODE_LIVE,
    EXECUTION_MODE_SHADOW,
    EXECUTION_STATE_COMMITTED,
    EXECUTION_STATE_SIMULATED,
    reject_new_mission,
)
from src.ugr.mission.mission_ledger import MissionLedger
from src.ugr.mission.mission_runtime import UGRMissionRuntime
from src.ugr.mission.step_execution import try_commit_execution


class TestExecutionPolicy(unittest.TestCase):
    def test_kill_switch_rejects_new_mission(self):
        os.environ["URG_MISSION_KILL_SWITCH"] = "1"
        try:
            rejected, reason = reject_new_mission(request={"intent": "demo"})
            self.assertTrue(rejected)
            self.assertIn("kill_switch", reason)
        finally:
            os.environ.pop("URG_MISSION_KILL_SWITCH", None)

    def test_execution_safety_blocks_without_manifold(self):
        results = check_execution_safety({}, {"organ_id": "o1", "provider": "local", "rail": "SAFE"})
        self.assertTrue(any(r.get("status") == "hard_fail" for r in results))


class TestExecutionModes(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-exec-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "exec-test-op-key"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "exec-test-urg-key"
        os.environ.pop("UGR_LLM_EXECUTE", None)
        os.environ.pop("URG_EXECUTION_MODE", None)
        os.environ.pop("URG_MISSION_KILL_SWITCH", None)
        hc_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo-healthcheck-embedding.json"
        self.healthcheck = json.loads(hc_path.read_text(encoding="utf-8"))["mission"]
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo-live.json"
        self.live_one_step = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    def tearDown(self):
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        os.environ.pop("URG_EXECUTION_MODE", None)
        os.environ.pop("URG_MISSION_KILL_SWITCH", None)
        os.environ.pop("UGR_LLM_EXECUTE", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _runtime(self) -> UGRMissionRuntime:
        return UGRMissionRuntime(runtime_dir=self.temp_root)

    def _ledger(self) -> MissionLedger:
        return MissionLedger(runtime_dir=self.temp_root, tenant_id="tenant:acme")

    def test_dry_run_simulated_no_provider_commit(self):
        payload = dict(self.healthcheck)
        payload["execution_mode"] = EXECUTION_MODE_DRY_RUN
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result.get("execution_mode"), EXECUTION_MODE_DRY_RUN)
        step = result["steps"][0]
        self.assertEqual(step.get("execution_state"), EXECUTION_STATE_SIMULATED)
        self.assertFalse(step.get("execution_committed"))
        rows = self._ledger().list_for_mission(result["mission_id"])
        phases = {r.get("phase") for r in rows if r.get("type") == "urg_mission_transition"}
        self.assertIn("mission_ingress", phases)
        self.assertIn("organ_assignment", phases)
        self.assertIn("provider_ack", phases)
        self.assertFalse(any(r.get("execution_committed") for r in rows))
        schema = result.get("mission_receipt_schema") or {}
        self.assertEqual(schema.get("outcome"), "completed")
        self.assertIsNone(schema.get("failure_reason"))

    @patch("src.ugr.mission.aais_step_bridge.run_governed_llm_lane")
    def test_shadow_execution_committed_with_discard(self, mock_lane):
        from src.ugr.lane_manager import LaneResult

        mock_lane.return_value = LaneResult(
            lane_id="mission-test-llm",
            lane_type="llm",
            status="success",
            metrics={"governed_llm_status": "PROPOSED", "execution_status": "EXECUTED"},
            invariant_results=[],
            immune_flags=[],
            payload={
                "governed_llm": {
                    "status": "PROPOSED",
                    "proposal_only": True,
                    "execution_authority": "none",
                    "provider_request": {"provider": "local"},
                },
                "governed_llm_execution": {
                    "status": "EXECUTED",
                    "tokens_used": 3,
                    "proposal_only": False,
                    "execution_authority": "governed",
                },
            },
        )
        payload = dict(self.healthcheck)
        payload["execution_mode"] = EXECUTION_MODE_SHADOW
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["steps"][0].get("execution_committed"))
        self.assertTrue(result["steps"][0].get("shadow"))
        self.assertTrue((result["steps"][0].get("aais_deliberation") or {}).get("downstream_discarded"))
        schema = result.get("mission_receipt_schema") or {}
        self.assertTrue(schema.get("shadow"))
        rows = self._ledger().list_for_mission(result["mission_id"])
        ack = [r for r in rows if r.get("phase") == "provider_ack"]
        self.assertTrue(ack)
        self.assertEqual(ack[-1].get("execution_state"), EXECUTION_STATE_COMMITTED)
        self.assertTrue(ack[-1].get("shadow"))

    def test_kill_switch_runtime_rejects(self):
        os.environ["URG_MISSION_KILL_SWITCH"] = "1"
        result = self._runtime().run_mission(self.healthcheck)
        self.assertEqual(result["status"], "rejected")

    def test_try_commit_requires_provider_ack(self):
        from src.ugr.invariants.cloud_manifold import build_cloud_manifold
        from src.ugr.mission.ingress import UrgIngressLaw

        payload = dict(self.healthcheck)
        ingress = UrgIngressLaw().stamp_mission(payload)
        manifold = build_cloud_manifold(
            request=payload,
            ingress=ingress,
            organ_ids=["organ-local-tiny"],
            rail="SAFE",
        )
        organ = self._runtime().organs.get("organ-local-tiny")
        ok, state, _ = try_commit_execution(
            mission_request=payload,
            ingress=ingress,
            step=payload["steps"][0],
            organ=organ,
            action_id="mid:step:1",
            mission_id=str(ingress["mission_id"]),
            manifold=manifold,
            invariants=self._runtime().invariants,
            step_invariants=[],
            rail="SAFE",
            provider_ack={"provider_acknowledged": False},
        )
        self.assertFalse(ok)
        self.assertNotEqual(state, EXECUTION_STATE_COMMITTED)

    @unittest.skipUnless(
        os.getenv("UGR_LLM_EXECUTE", "").strip().lower() in {"1", "true", "yes", "on"},
        "live provider execution requires UGR_LLM_EXECUTE=1",
    )
    def test_healthcheck_live_execution_committed(self):
        payload = dict(self.healthcheck)
        payload["execution_mode"] = EXECUTION_MODE_LIVE
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "ok")
        step = result["steps"][0]
        self.assertTrue(step.get("execution_committed"))
        self.assertFalse(step.get("shadow"))
        schema = result.get("mission_receipt_schema") or {}
        self.assertEqual(schema.get("outcome"), "completed")
        self.assertTrue(schema.get("cloud_identity_hash"))
        self.assertTrue(schema.get("boundary_digest"))
        self.assertTrue(schema.get("receipt_sig"))
        self.assertIsNone(schema.get("failure_reason"))
        rows = self._ledger().list_for_mission(result["mission_id"])
        phases = [r.get("phase") for r in rows if r.get("type") == "urg_mission_transition"]
        for required in ("mission_ingress", "organ_assignment", "provider_dispatch", "provider_ack"):
            self.assertIn(required, phases)
