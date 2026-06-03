"""Tests for UGR Proof-of-Subsystem discovery."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.discovery.subsystem_discovery import (
    SubsystemDiscoveryService,
    discovery_enabled,
)
from src.ugr.discovery.subsystem_discovery_receipt import verify_subsystem_discovery_receipt
from src.ugr.discovery.subsystem_spec import SubsystemSpec, subsystem_id_from_spec
from src.ugr.discovery.subsystem_validity import validate_subsystem_spec


def _valid_spec() -> dict:
    return {
        "role": "llm_executor",
        "io_shape": {"inputs": ["text"], "outputs": ["text"]},
        "rail_class": "NORMAL",
        "risk_ceiling": "low",
        "tenant_class": "standard",
    }


class TestSubsystemSpec(unittest.TestCase):
    def test_stable_hash(self):
        spec = SubsystemSpec.from_dict(_valid_spec())
        h1 = subsystem_id_from_spec(spec)
        h2 = subsystem_id_from_spec(spec.canonical_dict())
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


class TestSubsystemDiscovery(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-discovery-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "test-discovery-op-key"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-discovery-urg-key"
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "1"

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        os.environ.pop("UGR_SUBSYSTEM_DISCOVERY_ENABLED", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_discovery_enabled_default(self):
        os.environ.pop("UGR_SUBSYSTEM_DISCOVERY_ENABLED", None)
        self.assertTrue(discovery_enabled())

    def test_validate_subsystem_spec_acme(self):
        spec = SubsystemSpec.from_dict(_valid_spec())
        result = validate_subsystem_spec(
            spec,
            tenant_id="tenant:acme",
            operator_id="op-discovery",
            aais_instance_id="aais-test-1",
        )
        self.assertTrue(result.valid, result.errors)
        self.assertTrue(result.organs_matched)
        self.assertTrue(any(i.get("status") == "pass" for i in result.invariants))

    def test_discover_emits_receipt(self):
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        payload = {
            "tenant_id": "tenant:acme",
            "operator_id": "op-discovery",
            "aais_instance_id": "aais-test-1",
            "spec": _valid_spec(),
        }
        result = service.discover(payload)
        self.assertEqual(result.get("status"), "discovered")
        sid = result.get("subsystem_id")
        self.assertTrue(sid)
        receipt = result.get("subsystem_discovery_receipt") or {}
        ok, reason = verify_subsystem_discovery_receipt(receipt, runtime_dir=str(self.temp_root))
        self.assertTrue(ok, reason)

    def test_idempotent_rediscover(self):
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        payload = {
            "tenant_id": "tenant:acme",
            "operator_id": "op-discovery",
            "aais_instance_id": "aais-test-1",
            "spec": _valid_spec(),
        }
        first = service.discover(payload)
        second = service.discover(payload)
        self.assertEqual(first.get("subsystem_id"), second.get("subsystem_id"))
        self.assertTrue(second.get("idempotent"))

    def test_invalid_spec(self):
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        bad = dict(_valid_spec())
        bad["role"] = "nonexistent_role_xyz"
        result = service.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-discovery",
                "aais_instance_id": "aais-test-1",
                "spec": bad,
            }
        )
        self.assertEqual(result.get("status"), "invalid")

    def test_search_from_seed(self):
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        result = service.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-discovery",
                "aais_instance_id": "aais-test-1",
                "seed": {"tenant_class": "standard", "io_shape": {"inputs": ["text"], "outputs": ["text"]}},
                "constraints": {
                    "roles": ["llm_executor"],
                    "rail_classes": ["NORMAL"],
                    "risk_ceilings": ["low"],
                    "tenant_classes": ["standard"],
                },
                "max_attempts": 32,
            }
        )
        self.assertEqual(result.get("status"), "discovered")
        receipt = result.get("subsystem_discovery_receipt") or {}
        self.assertEqual(receipt.get("discovery_mode"), "search")
        self.assertGreater(int(receipt.get("search_attempts") or 0), 0)

    def test_tenant_isolation(self):
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        payload = {
            "tenant_id": "tenant:acme",
            "operator_id": "op-discovery",
            "aais_instance_id": "aais-test-1",
            "spec": _valid_spec(),
        }
        discovered = service.discover(payload)
        sid = discovered.get("subsystem_id")
        cross = service.get_receipt(sid, tenant_id="tenant:contoso")
        self.assertIsNone(cross)
        local = service.get_receipt(sid, tenant_id="tenant:acme")
        self.assertIsNotNone(local)

    def test_catalog_list(self):
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        service.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-discovery",
                "aais_instance_id": "aais-test-1",
                "spec": _valid_spec(),
            }
        )
        entries = service.list_discoveries(tenant_id="tenant:acme")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].get("status"), "shadow")

    def test_global_tenant_class(self):
        spec = SubsystemSpec.from_dict(
            {
                **_valid_spec(),
                "tenant_class": "global",
                "rail_class": "SAFE",
            }
        )
        result = validate_subsystem_spec(
            spec,
            tenant_id="global",
            operator_id="op-discovery",
            aais_instance_id="aais-test-1",
        )
        self.assertTrue(result.valid, result.errors)

    def test_discovery_disabled(self):
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "0"
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        result = service.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-discovery",
                "aais_instance_id": "aais-test-1",
                "spec": _valid_spec(),
            }
        )
        self.assertEqual(result.get("status"), "rejected")

    def test_promote_blocked_without_governance_apply(self):
        service = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        os.environ.pop("URG_GOVERNANCE_APPLY", None)
        result = service.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-discovery",
                "aais_instance_id": "aais-test-1",
                "spec": _valid_spec(),
                "promote": True,
            }
        )
        self.assertEqual(result.get("status"), "discovered")
        promotion = result.get("promotion") or {}
        self.assertEqual(promotion.get("status"), "blocked")


if __name__ == "__main__":
    unittest.main()
