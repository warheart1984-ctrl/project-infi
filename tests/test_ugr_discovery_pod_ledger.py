"""Tests for Discovery Pod append-only ledger."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.discovery.discovery_pod_ledger import (
    DiscoveryPodLedger,
    operator_id_from_display_name,
    pod_id_from_display_name,
    slugify_pod_name,
)


class TestDiscoveryPodLedger(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-pod-ledger-"))
        self.ledger_path = self.temp_root / "discovery-pods.jsonl"
        self.registry_path = self.temp_root / "discovery-pods.json"
        self.ledger = DiscoveryPodLedger(
            ledger_path=self.ledger_path,
            registry_path=self.registry_path,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_slugify(self):
        self.assertEqual(slugify_pod_name("Jon Halstead"), "jon-halstead")
        self.assertEqual(pod_id_from_display_name("Jon Halstead"), "pod:jon-halstead")
        self.assertEqual(operator_id_from_display_name("Jon Halstead"), "operator:jon-halstead")

    def test_register_appends_ledger_and_syncs_registry(self):
        result = self.ledger.register(
            "Jon Halstead",
            label="First Pod",
            notes="seed",
            registered_by="test",
        )
        self.assertTrue(result.ok)
        self.assertFalse(result.idempotent)
        self.assertEqual(result.pod_index, 1)
        self.assertTrue(self.ledger_path.exists())
        lines = [ln for ln in self.ledger_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        row = json.loads(lines[0])
        self.assertEqual(row["display_name"], "Jon Halstead")
        self.assertEqual(row["event_type"], "pod_registered")

        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.assertIn("pod:jon-halstead", registry["pods"])
        self.assertEqual(registry["pods"]["pod:jon-halstead"]["display_name"], "Jon Halstead")

    def test_register_is_idempotent_for_same_name(self):
        first = self.ledger.register("Ada Lovelace")
        second = self.ledger.register("Ada Lovelace")
        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertTrue(second.idempotent)
        self.assertEqual(first.pod_id, second.pod_id)
        lines = [ln for ln in self.ledger_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)

    def test_sequential_pod_index(self):
        self.ledger.register("Jon Halstead")
        second = self.ledger.register("Second Pod Member")
        self.assertEqual(second.pod_index, 2)
        pods = self.ledger.list_pods()
        self.assertEqual(len(pods), 2)

    def test_record_discovery_auto_registers_and_upgrades(self):
        result = self.ledger.record_discovery(
            operator_id="operator:ada-lovelace",
            tenant_id="tenant:acme",
            contribution_id="contrib-001",
            contribution_type="proof",
            spec_payload={"discovery_pod_id": "pod:ada-lovelace", "pod_display_name": "Ada Lovelace"},
            receipt_id="receipt-001",
        )
        self.assertTrue(result.ok)
        self.assertTrue(result.newly_registered)
        self.assertEqual(result.discovery_count, 1)

        second = self.ledger.record_discovery(
            operator_id="operator:ada-lovelace",
            tenant_id="tenant:acme",
            contribution_id="contrib-002",
            contribution_type="workflow",
            spec_payload={"discovery_pod_id": "pod:ada-lovelace"},
            receipt_id="receipt-002",
        )
        self.assertTrue(second.ok)
        self.assertFalse(second.newly_registered)
        self.assertEqual(second.discovery_count, 2)

        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        pod = registry["pods"]["pod:ada-lovelace"]
        self.assertEqual(pod["discovery_count"], 2)
        self.assertEqual(pod["last_contribution_id"], "contrib-002")

    def test_record_discovery_infers_pod_from_operator_id(self):
        receipt = {
            "receipt_sig": "signed",
            "invariants_passed": [{"status": "pass", "family": "workflow"}],
        }
        result = self.ledger.record_discovery(
            operator_id="operator:grace-hopper",
            tenant_id="global",
            contribution_id="contrib-hopper-1",
            contribution_type="workflow",
            spec_payload={},
            receipt_id="receipt-hopper-1",
            receipt=receipt,
            receipt_verified=True,
        )
        self.assertTrue(result.ok)
        self.assertFalse(result.skipped)
        self.assertEqual(result.pod_id, "pod:grace-hopper")
        self.assertEqual(result.display_name, "Grace Hopper")


if __name__ == "__main__":
    unittest.main()
