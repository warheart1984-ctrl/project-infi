"""Golden tests for URG v1.5 cloud invariant layer."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ugr.invariants.cloud_invariants import (
    check_cloud_causality,
    check_cloud_identity,
    check_cloud_mutation,
    has_hard_fail,
)
from src.ugr.invariants.cloud_manifold import build_cloud_manifold, compute_cloud_identity_hash
from src.ugr.mission.composite_mission import ReceiptBuildError, issue_mission_receipt
from src.ugr.mission.governance_mission import is_governance_mission, run_governance_mission
from src.ugr.mission.mission_ledger import MissionLedger
from src.ugr.mission.mission_receipt import FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS
from src.ugr.mission.mission_runtime import UGRMissionRuntime


class TestCloudManifold(unittest.TestCase):
    def test_identity_hash_stable(self):
        h1 = compute_cloud_identity_hash(
            tenant_id="t1",
            operator_id="op1",
            mission_id="mid",
            organ_ids=["a", "b"],
            region_ids=["tenant-us"],
            aais_instance_id="aais-1",
        )
        h2 = compute_cloud_identity_hash(
            tenant_id="t1",
            operator_id="op1",
            mission_id="mid",
            organ_ids=["b", "a"],
            region_ids=["tenant-us"],
            aais_instance_id="aais-1",
        )
        self.assertEqual(h1, h2)


class TestCloudInvariantGolden(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-cloud-inv-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "cloud-test-op-key"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "cloud-test-urg-key"
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json"
        self.demo = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    def tearDown(self):
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        os.environ.pop("URG_GOVERNANCE_OPERATOR_ALLOWLIST", None)
        os.environ.pop("URG_GOVERNANCE_AUTHORITY_TOKEN", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _runtime(self) -> UGRMissionRuntime:
        return UGRMissionRuntime(runtime_dir=self.temp_root)

    def _ledger(self) -> MissionLedger:
        return MissionLedger(runtime_dir=self.temp_root, tenant_id="tenant:acme")

    def test_out_of_region_organ_blocked(self):
        payload = dict(self.demo)
        payload["constraints"] = dict(payload.get("constraints") or {})
        payload["constraints"]["required_region"] = "tenant-eu"
        payload["region_id"] = "tenant-us"
        result = self._runtime().run_mission(payload)
        self.assertIn(result["status"], {"blocked", "rejected"})
        schema = result.get("mission_receipt_schema") or {}
        if schema.get("failure_reason"):
            self.assertEqual(schema["failure_reason"], FAILURE_REASON_UNFULFILLABLE_CONSTRAINTS)
        if schema:
            self.assertTrue(schema.get("cloud_identity_hash"))
            self.assertTrue(schema.get("boundary_digest"))

    def test_duplicate_step_id_blocked(self):
        payload = dict(self.demo)
        steps = list(payload["steps"])
        steps[1]["step_id"] = steps[0]["step_id"]
        payload["steps"] = steps
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "blocked")

    def test_identity_drift_without_rebind(self):
        ingress = {"mission_id": "m1", "cloud_identity_hash": "abc", "status": "stamped"}
        results = check_cloud_identity(
            {
                "request": {"operator_id": "op", "aais_instance_id": "a1", "tenant_id": "t"},
                "ingress": ingress,
                "cloud_manifold": {"cloud_identity_hash": "abc", "organ_ids": []},
                "organ_ids": [],
            },
            authorized_rebind=False,
        )
        self.assertTrue(has_hard_fail(results))

    def test_causality_missing_ledger_entry(self):
        steps = [{"step_id": "s1", "status": "ok", "action_id": "m:s1:1"}]
        results = check_cloud_causality([], steps, mission_id="m")
        self.assertTrue(has_hard_fail(results))

    def test_receipt_refuses_causality_tamper(self):
        result = self._runtime().run_mission(self.demo)
        gcm = result["governed_composite_mission"]
        ingress = result["urg_ingress"]
        ledger_rows = MissionLedger(runtime_dir=self.temp_root).list_for_mission(result["mission_id"])
        tampered = list(ledger_rows)
        action_rows = [r for r in tampered if r.get("type") == "urg_mission_action"]
        if action_rows:
            idx = tampered.index(action_rows[0])
            tampered[idx] = dict(tampered[idx])
            tampered[idx]["action_id"] = "tampered"
        with self.assertRaises(ReceiptBuildError):
            issue_mission_receipt(
                dict(gcm, status="ok"),
                ingress=ingress,
                enforcement_summary="tamper",
                ledger_rows=tampered,
                steps=result["steps"],
                request=self.demo,
                runtime_dir=str(self.temp_root),
            )

    def test_governance_mutation_unauthorized(self):
        payload = {
            "mission_kind": "governance_mutation",
            "mutation_target": "provider_organs",
            "operator_id": "not-allowed",
        }
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "rejected")

    def test_governance_mutation_authorized(self):
        os.environ["URG_GOVERNANCE_OPERATOR_ALLOWLIST"] = "gov-operator"
        payload = {
            "mission_kind": "governance_mutation",
            "mutation_target": "provider_organs",
            "operator_id": "gov-operator",
            "aais_instance_id": "aais-primary",
            "tenant_id": "tenant:acme",
            "region_id": "tenant-us",
            "steps": [{"step_id": "gov", "objective": "mutate"}],
        }
        result = self._runtime().run_mission(payload)
        self.assertEqual(result["status"], "ok")
        rows = self._ledger().list_for_mission(result["mission_id"])
        self.assertTrue(any(r.get("type") == "governance_mutation" for r in rows))
        schema = result["mission_receipt_schema"]
        self.assertEqual(schema["schema_version"], "1.4")
        self.assertTrue(schema.get("cloud_identity_hash"))

    def test_completed_receipt_has_cloud_proof_fields(self):
        result = self._runtime().run_mission(self.demo)
        schema = result["mission_receipt_schema"]
        self.assertEqual(schema["schema_version"], "1.4")
        self.assertEqual(schema["invariant_version"], "3.0")
        self.assertTrue(schema.get("cloud_identity_hash"))
        self.assertTrue(schema.get("boundary_digest"))
        for organ in schema["organs"]:
            self.assertIn("region_id", organ)
            self.assertIn("rail", organ)


class TestGovernanceHelpers(unittest.TestCase):
    def test_is_governance_mission(self):
        self.assertTrue(is_governance_mission({"mission_kind": "governance_mutation"}))
        self.assertFalse(is_governance_mission({"intent": "demo"}))
