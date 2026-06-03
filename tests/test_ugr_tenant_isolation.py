"""Tests for URG multi-tenant isolation (Phase 1)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.mission_receipt_store import MissionReceiptStore, receipt_admin_enabled
from src.ugr.mission.mission_runtime import UGRMissionRuntime
from src.ugr.mission.tenant_manifold import validate_tenant_for_mission
from src.ugr.platform.tenant_registry import normalize_tenant_id


class TestTenantManifold(unittest.TestCase):
    def test_unknown_tenant_rejected(self):
        manifold, results = validate_tenant_for_mission({"tenant_id": "tenant:unknown-corp"})
        self.assertIsNone(manifold)
        self.assertTrue(any(r.get("status") == "hard_fail" for r in results))

    def test_acme_tenant_passes(self):
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json"
        mission = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]
        manifold, results = validate_tenant_for_mission(mission)
        self.assertIsNotNone(manifold)
        self.assertEqual(manifold.tenant_id, "tenant:acme")
        self.assertFalse(any(r.get("status") == "hard_fail" for r in results))


class TestTenantPartitioning(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-tenant-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "tenant-test-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "tenant-test-urg"
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json"
        self.demo = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    def tearDown(self):
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        os.environ.pop("URG_RECEIPT_ADMIN", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_ledger_partitioned_by_tenant(self):
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(self.demo)
        self.assertEqual(result["status"], "ok")
        ledger_path = (
            self.temp_root
            / "collective-pattern-ledger"
            / "tenants"
            / "tenant-acme"
            / "missions.jsonl"
        )
        self.assertTrue(ledger_path.exists())

    def test_receipt_cross_tenant_denied_without_admin(self):
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(self.demo)
        mission_id = result["mission_id"]
        store_acme = MissionReceiptStore(runtime_dir=self.temp_root, tenant_id="tenant:acme")
        record = store_acme.get_receipt(mission_id, tenant_id="tenant:acme")
        self.assertIsNotNone(record)
        store_contoso = MissionReceiptStore(runtime_dir=self.temp_root, tenant_id="tenant:contoso")
        self.assertIsNone(store_contoso.get_receipt(mission_id, tenant_id="tenant:contoso"))

    def test_federation_without_grant_blocked(self):
        payload = dict(self.demo)
        payload["federation_target_tenant"] = "tenant:contoso"
        payload["federation_grant_id"] = "missing-grant"
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(payload)
        self.assertEqual(result["status"], "rejected")

    def test_ingress_normalizes_tenant_id(self):
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(self.demo)
        self.assertEqual(
            normalize_tenant_id(result["urg_ingress"]["tenant_id"]),
            "tenant:acme",
        )
        self.assertTrue(result["urg_ingress"].get("tenant_manifold_digest"))


class TestTenantReceiptSchema(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-tenant-r-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "tenant-test-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "tenant-test-urg"
        self.demo = json.loads(
            (Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json").read_text(
                encoding="utf-8"
            )
        )["mission"]

    def tearDown(self):
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_receipt_has_tenant_proof_fields(self):
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(self.demo)
        schema = result.get("mission_receipt_schema") or {}
        self.assertEqual(schema.get("tenant_normalized_id"), "tenant:acme")
        self.assertTrue(schema.get("tenant_manifold_digest"))
