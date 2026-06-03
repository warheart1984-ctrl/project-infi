"""Tests for URG mission-level Governed Composite Mission v1.4."""

import json
import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from src.ugr.mission.cloud_invariants import CloudInvariantEvaluator
from src.ugr.mission.ingress import UrgIngressLaw
from src.ugr.mission.ledger_merkle import compute_ledger_merkle_root, transition_leaf_hash
from src.ugr.mission.mission_ledger import MissionLedger
from src.ugr.mission.mission_receipt import (
    FAILURE_REASON_GATE_REJECTION,
    FAILURE_REASON_NO_ADMISSIBLE_ORGAN,
    FAILURE_REASON_OPERATOR_VETO,
    FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS,
    build_goal_hash,
    map_failure_reason,
    map_outcome,
    OUTCOME_VETOED,
)
from src.ugr.mission.mission_receipt_store import MissionReceiptStore
from src.ugr.mission.mission_runtime import UGRMissionRuntime, URG_MISSION_RUNTIME_VERSION
from src.ugr.mission.organ_matcher import resolve_step_organ
from src.ugr.mission.provider_organ import ProviderOrganRegistry
from src.ugr.mission.composite_mission import _collect_aais_step_summaries
from src.ugr.mission.receipt_signing import (
    ALGORITHM_HMAC,
    verify_mission_receipt,
    verify_mission_receipt_v2,
)


class TestUrgIngress(unittest.TestCase):
    def test_stamp_and_validate(self):
        law = UrgIngressLaw()
        ingress = law.stamp_mission({"operator_id": "op1", "aais_instance_id": "aais-1", "intent": "demo"})
        ok, reason = law.validate_stamp(ingress)
        self.assertTrue(ok, reason)
        uuid.UUID(str(ingress.get("mission_id")))
        self.assertTrue(ingress.get("mission_slug"))


class TestProviderOrgans(unittest.TestCase):
    def test_three_demo_organs_loaded(self):
        registry = ProviderOrganRegistry()
        ids = registry.admitted_organ_ids()
        self.assertIn("organ-local-tiny", ids)
        self.assertIn("organ-openrouter-mid", ids)
        self.assertIn("organ-openai-big", ids)


class TestMissionDemo(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-mission-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "test-receipt-key-fixed"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-urg-receipt-key-fixed"
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json"
        self.demo = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]
        auto_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo-auto.json"
        self.demo_auto = json.loads(auto_path.read_text(encoding="utf-8"))["mission"]

    def tearDown(self):
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _runtime(self) -> UGRMissionRuntime:
        return UGRMissionRuntime(runtime_dir=self.temp_root)

    def _ledger(self) -> MissionLedger:
        return MissionLedger(runtime_dir=self.temp_root, tenant_id="tenant:acme")

    def _receipt_store(self) -> MissionReceiptStore:
        return MissionReceiptStore(runtime_dir=self.temp_root, tenant_id="tenant:acme")

    def test_one_mission_three_providers_ledgered(self):
        result = self._runtime().run_mission(self.demo)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["steps"]), 3)
        providers = {step["provider"] for step in result["steps"]}
        self.assertEqual(providers, {"local", "openrouter", "openai"})
        self.assertTrue(result["urg_ingress"].get("stamp_hash"))
        self.assertEqual(len(result["ledger_refs"]), 3)
        rows = self._ledger().list_for_mission(result["mission_id"])
        action_rows = [r for r in rows if r.get("type") == "urg_mission_action"]
        self.assertEqual(len(action_rows), 3)
        self.assertEqual(action_rows[0].get("prior_action_id"), None)
        self.assertEqual(action_rows[1].get("prior_action_id"), action_rows[0].get("action_id"))
        self.assertEqual(action_rows[2].get("prior_action_id"), action_rows[1].get("action_id"))
        phases = {r.get("phase") for r in rows if r.get("type") == "urg_mission_transition"}
        self.assertIn("mission_ingress", phases)

    def test_region_constraint_blocks_wrong_region(self):
        payload = dict(self.demo)
        payload["region_id"] = "tenant-eu"
        result = self._runtime().run_mission(payload)
        self.assertIn(result["status"], {"blocked", "rejected"})

    def test_cost_budget_blocks_overspend(self):
        payload = dict(self.demo)
        payload["constraints"] = dict(payload.get("constraints") or {})
        payload["constraints"]["max_total_cost_units"] = 5
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "blocked")

    def test_switchboard_not_model(self):
        result = self._runtime().run_mission(self.demo)
        self.assertEqual(result["switchboard"]["role"], "lawbook_not_model")
        self.assertTrue(result["switchboard"].get("aais_step_bridge"))
        for step in result["steps"]:
            self.assertTrue(step["proposal"]["proposal_only"])
            self.assertEqual(step["proposal"]["execution_authority"], "none")

    def test_governed_composite_mission_tuple(self):
        result = self._runtime().run_mission(self.demo)
        gcm = result["governed_composite_mission"]
        self.assertEqual(gcm["atomic_unit"], "governed_composite_mission")
        self.assertEqual(gcm["gcm_version"], "1.9")
        self.assertIn("goal", gcm)
        self.assertIn("constraints", gcm)
        self.assertIn("participating_organs", gcm)
        self.assertIn("invariant_set", gcm)
        self.assertIn("ledger_trail", gcm)
        self.assertEqual(len(gcm["participating_organs"]), 3)
        self.assertEqual(gcm["invariant_set"]["all_passed"], True)
        action_entries = [
            e for e in gcm["ledger_trail"]["entries"] if e.get("type") == "urg_mission_action"
        ]
        self.assertEqual(len(action_entries), 3)

    def test_signed_mission_receipt_hmac(self):
        result = self._runtime().run_mission(self.demo)
        receipt = result["mission_receipt"]
        self.assertEqual(receipt["receipt_algorithm"], ALGORITHM_HMAC)
        self.assertIsNotNone(receipt.get("receipt_mac"))
        self.assertEqual(len(receipt["content_digest"]), 64)
        self.assertEqual(receipt["ingress_stamp_hash"], result["urg_ingress"]["stamp_hash"])
        ok, reason = verify_mission_receipt(
            receipt,
            result["governed_composite_mission"],
            ingress=result["urg_ingress"],
            key="test-receipt-key-fixed",
            aais_step_summaries=_collect_aais_step_summaries(result["steps"]),
        )
        self.assertTrue(ok, reason)

    def test_urg_phases_decompose_assign_enforce(self):
        result = self._runtime().run_mission(self.demo)
        phases = result["urg_phases"]
        self.assertEqual(phases["decompose"]["step_count"], 3)
        self.assertEqual(len(phases["assign"]["assignments"]), 3)
        self.assertEqual(len(phases["enforce"]["steps"]), 3)

    def test_step_uses_real_bridge(self):
        result = self._runtime().run_mission(self.demo)
        for step in result["steps"]:
            deliberation = step.get("aais_deliberation") or {}
            self.assertIn("bridge", deliberation)
            bridge = deliberation["bridge"]
            self.assertIn(str(bridge.get("decision", "")).upper(), {"ALLOW", "DEGRADE"})
            self.assertEqual(deliberation.get("mode"), "llm_bridge")

    def test_routing_only_without_aais_bridge(self):
        payload = dict(self.demo)
        payload["aais_step_bridge"] = False
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["switchboard"].get("aais_step_bridge"))
        for step in result["steps"]:
            self.assertIsNone(step.get("aais_deliberation"))

    def test_full_deliberate_mode(self):
        payload = dict(self.demo)
        payload["step_deliberation_mode"] = "full_deliberate"
        payload["steps"] = [payload["steps"][0]]
        with patch("src.ugr.mission.aais_step_bridge.run_full_deliberate_step") as mock_full:
            mock_full.return_value = {
                "mode": "full_deliberate",
                "status": "ok",
                "bridge_decision": "ALLOW",
                "bridge": {"decision": "ALLOW"},
                "deliberation": {"status": "ok", "summary": "mocked"},
                "lane_results": [],
                "governed_llm_status": "PROPOSED",
                "proposal": {"status": "PROPOSED", "proposal_only": True, "execution_authority": "none"},
                "summary": "mocked full deliberate",
            }
            result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "ok")
        mock_full.assert_called_once()
        self.assertEqual(result["steps"][0]["aais_deliberation"]["mode"], "full_deliberate")

    def test_auto_assign_three_providers(self):
        result = self._runtime().run_mission(self.demo_auto)
        self.assertEqual(result["status"], "ok")
        providers = {step["provider"] for step in result["steps"]}
        self.assertEqual(providers, {"local", "openrouter", "openai"})
        assignments = result["urg_phases"]["assign"]["assignments"]
        self.assertTrue(any(a.get("auto_assigned") for a in assignments))

    def test_auto_assign_budget_blocks(self):
        payload = dict(self.demo_auto)
        payload["constraints"] = dict(payload.get("constraints") or {})
        payload["constraints"]["max_total_cost_units"] = 5
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "blocked")

    def test_mission_receipt_schema_fields(self):
        result = self._runtime().run_mission(self.demo)
        schema = result["mission_receipt_schema"]
        self.assertEqual(schema["schema_version"], "1.4")
        self.assertEqual(schema["urg_version"], URG_MISSION_RUNTIME_VERSION)
        self.assertEqual(schema["invariant_version"], "3.0")
        self.assertTrue(schema.get("cloud_identity_hash"))
        self.assertTrue(schema.get("boundary_digest"))
        uuid.UUID(schema["mission_id"])
        self.assertEqual(len(schema["goal_hash"]), 64)
        self.assertEqual(len(schema["organs"]), 3)
        self.assertEqual(len(schema["invariant_digest"]), 64)
        self.assertEqual(len(schema["ledger_root"]), 64)
        self.assertEqual(schema["outcome"], "completed")
        self.assertNotIn("failure_reason", schema)
        self.assertIsNotNone(schema.get("receipt_sig"))
        self.assertIn("operator_mac", schema["operator_sig"])
        self.assertEqual(schema["operator_sig"]["operator_key_id"], "env:URG_OPERATOR_RECEIPT_KEY")
        self.assertEqual(schema["urg_key_id"], "env:URG_RECEIPT_SIGNING_KEY")

    def test_failure_reason_no_admissible_organ(self):
        payload = dict(self.demo)
        payload["steps"] = [
            {
                "step_id": "no-organ",
                "objective": "unassignable",
                "tier": "nonexistent-tier-xyz",
            }
        ]
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "blocked")
        schema = result["mission_receipt_schema"]
        self.assertEqual(schema["failure_reason"], FAILURE_REASON_NO_ADMISSIBLE_ORGAN)

    def test_failure_reason_unfulfillable_constraints(self):
        payload = dict(self.demo)
        payload["constraints"] = dict(payload.get("constraints") or {})
        payload["constraints"]["required_region"] = "tenant-eu"
        payload["region_id"] = "tenant-us"
        result = self._runtime().run_mission(payload)
        self.assertIn(result["status"], {"blocked", "rejected"})
        schema = result.get("mission_receipt_schema") or {}
        if schema.get("failure_reason"):
            self.assertEqual(schema["failure_reason"], FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS)

    def test_failure_reason_operator_veto_enum(self):
        reason = map_failure_reason(
            status="blocked",
            request={"operator_veto": True},
        )
        self.assertEqual(reason, FAILURE_REASON_OPERATOR_VETO)

    def test_failure_reason_gate_rejection_enum(self):
        self.assertEqual(map_failure_reason(status="rejected"), FAILURE_REASON_GATE_REJECTION)

    def test_receipt_persisted_across_runtime_restart(self):
        result = self._runtime().run_mission(self.demo)
        mission_id = result["mission_id"]
        record = self._receipt_store().get_receipt(mission_id, tenant_id="tenant:acme")
        self.assertIsNotNone(record)
        schema = record["mission_receipt_schema"]
        ledger_rows = self._ledger().list_for_mission(mission_id)
        ok, verify_reason = verify_mission_receipt_v2(
            schema,
            gcm=result["governed_composite_mission"],
            ingress=result["urg_ingress"],
            ledger_rows=ledger_rows,
            operator_key="test-receipt-key-fixed",
            urg_key="test-urg-receipt-key-fixed",
        )
        self.assertTrue(ok, verify_reason)
        second = UGRMissionRuntime(runtime_dir=self.temp_root)
        again = self._receipt_store().get_receipt(mission_id, tenant_id="tenant:acme")
        self.assertIsNotNone(again)
        self.assertEqual(again["mission_receipt_schema"]["mission_id"], mission_id)

    def test_gcm_participating_aais_instances(self):
        result = self._runtime().run_mission(self.demo)
        gcm = result["governed_composite_mission"]
        self.assertIn("participating_aais_instances", gcm)
        self.assertTrue(len(gcm["participating_aais_instances"]) >= 1)
        self.assertIn(str(self.demo.get("aais_instance_id")), gcm["participating_aais_instances"])

    def test_goal_hash_stable(self):
        goal = {"intent": "demo", "objective": "test", "operator_id": "op1", "tenant_id": "t1", "aais_instance_id": "a1", "region_id": "r1"}
        constraints = {"max_total_cost_units": 10}
        h1 = build_goal_hash(goal, constraints)
        h2 = build_goal_hash(goal, constraints)
        self.assertEqual(h1, h2)

    def test_ledger_merkle_root_changes_on_tamper(self):
        row = {"action_id": "m:s:1", "mission_id": "m", "step_id": "s"}
        root1 = compute_ledger_merkle_root([row])
        tampered = dict(row)
        tampered["status"] = "tampered"
        root2 = compute_ledger_merkle_root([tampered])
        self.assertNotEqual(root1, root2)
        self.assertEqual(transition_leaf_hash(row), transition_leaf_hash(dict(row)))

    def test_dual_sign_verify(self):
        result = self._runtime().run_mission(self.demo)
        schema = result["mission_receipt_schema"]
        ledger_rows = self._ledger().list_for_mission(result["mission_id"])
        ok, reason = verify_mission_receipt_v2(
            schema,
            gcm=result["governed_composite_mission"],
            ingress=result["urg_ingress"],
            ledger_rows=ledger_rows,
            operator_key="test-receipt-key-fixed",
            urg_key="test-urg-receipt-key-fixed",
        )
        self.assertTrue(ok, reason)

    def test_outcome_vetoed_on_rejected_mission(self):
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission({"steps": []})
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(map_outcome("rejected"), OUTCOME_VETOED)

    @unittest.skipUnless(
        os.getenv("UGR_LLM_EXECUTE", "").strip().lower() in {"1", "true", "yes", "on"},
        "requires UGR_LLM_EXECUTE=1",
    )
    def test_live_organ_mission_when_execute_enabled(self):
        live_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo-live.json"
        mission = json.loads(live_path.read_text(encoding="utf-8"))["mission"]
        result = self._runtime().run_mission(mission)
        self.assertEqual(result["status"], "ok")
        schema = result["mission_receipt_schema"]
        self.assertEqual(schema["outcome"], "completed")
        rows = MissionLedger(runtime_dir=self.temp_root).list_for_mission(result["mission_id"])
        self.assertTrue(any(r.get("execution_committed") for r in rows))


class TestOrganMatcher(unittest.TestCase):
    def test_resolve_by_tier(self):
        registry = ProviderOrganRegistry()
        organ, meta = resolve_step_organ(
            {"tier": "mid"},
            ordinal=1,
            step_count=3,
            organ_registry=registry,
            region_id="tenant-us",
            intent="governed_super_router_demo",
            constraints={"max_total_cost_units": 25, "risk_ceiling": "medium"},
        )
        self.assertIsNotNone(organ)
        self.assertEqual(organ.organ_id, "organ-openrouter-mid")
        self.assertTrue(meta.get("auto_assigned"))


class TestReceiptSigning(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-receipt-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)

    def tearDown(self):
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_content_only_without_key(self):
        from src.ugr.mission.receipt_signing import (
            ALGORITHM_CONTENT_ONLY,
            sign_receipt_payload,
            build_receipt_canonical_payload,
        )

        gcm = {"gcm_version": "1.2", "mission_id": "m1", "status": "ok", "goal": {}, "constraints": {},
               "participating_organs": [], "invariant_set": {"all_passed": True}, "ledger_trail": {"action_ids": []}}
        ingress = {"stamp_hash": "abc"}
        canonical = build_receipt_canonical_payload(gcm, ingress=ingress)
        signed = sign_receipt_payload(
            canonical, operator_id="op-no-key", runtime_dir=self.temp_root, create_key_if_missing=False
        )
        self.assertEqual(signed["receipt_algorithm"], ALGORITHM_CONTENT_ONLY)
        self.assertIsNone(signed.get("receipt_mac"))

    def test_verify_rejects_tamper(self):
        from src.ugr.mission.receipt_signing import sign_receipt_payload, build_receipt_canonical_payload

        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "tamper-test-key"
        gcm = {
            "gcm_version": "1.2",
            "mission_id": "m1",
            "status": "ok",
            "goal": {"operator_id": "op1"},
            "constraints": {},
            "participating_organs": [],
            "invariant_set": {"all_passed": True},
            "ledger_trail": {"action_ids": ["a1"]},
        }
        ingress = {"stamp_hash": "abc", "operator_id": "op1"}
        canonical = build_receipt_canonical_payload(gcm, ingress=ingress)
        signed = sign_receipt_payload(canonical, operator_id="op1")
        receipt = {
            "content_digest": signed["content_digest"],
            "receipt_mac": signed["receipt_mac"],
            "receipt_signature": signed["receipt_signature"],
            "receipt_algorithm": signed["receipt_algorithm"],
            "operator_id": "op1",
        }
        tampered = dict(gcm)
        tampered["status"] = "blocked"
        ok, reason = verify_mission_receipt(receipt, tampered, ingress=ingress, key="tamper-test-key")
        self.assertFalse(ok)
        self.assertIn("mismatch", reason)


class TestCloudInvariants(unittest.TestCase):
    def test_open_invariants_pass_for_demo(self):
        law = UrgIngressLaw()
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json"
        mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]
        ingress = law.stamp_mission(mission)
        results = CloudInvariantEvaluator().evaluate_mission_open(mission, ingress=ingress)
        self.assertFalse(CloudInvariantEvaluator.has_hard_fail(results))
