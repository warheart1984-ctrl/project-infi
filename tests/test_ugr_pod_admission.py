"""Tests for automatic Discovery Pod admission policy."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.discovery.discovery_pod_ledger import DiscoveryPodLedger
from src.ugr.discovery.pod_admission import (
    evaluate_pod_admission,
    load_pod_admission_policy,
    min_invariant_pass_count_from_policy,
)
from src.ugr.discovery.subsystem_discovery import SubsystemDiscoveryService


class TestPodAdmission(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-pod-admit-"))
        self.policy_path = self.temp_root / "admission.json"
        os.environ["UGR_DISCOVERY_POD_ADMISSION_POLICY_PATH"] = str(self.policy_path)

    def tearDown(self):
        os.environ.pop("UGR_DISCOVERY_POD_ADMISSION_POLICY_PATH", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_explicit_pod_fields_always_admit(self):
        verdict = evaluate_pod_admission(
            operator_id="operator:random-user",
            contribution_type="capability",
            spec_payload={"pod_display_name": "Random User"},
        )
        self.assertTrue(verdict.eligible)
        self.assertEqual(verdict.reason, "explicit_pod_fields")

    def test_proven_contribution_admits(self):
        receipt = {
            "payload": {"claim_label": "proven"},
            "receipt_sig": "signed",
            "invariants_passed": [{"status": "pass"}],
        }
        verdict = evaluate_pod_admission(
            operator_id="operator:jon-halstead",
            contribution_type="proof",
            receipt=receipt,
            receipt_verified=True,
        )
        self.assertTrue(verdict.eligible)
        self.assertEqual(verdict.reason, "proven_contribution")

    def test_workflow_admits_with_verified_receipt(self):
        receipt = {
            "receipt_sig": "signed",
            "invariants_passed": [{"status": "pass", "family": "workflow"}],
        }
        verdict = evaluate_pod_admission(
            operator_id="operator:grace-hopper",
            contribution_type="workflow",
            receipt=receipt,
            receipt_verified=True,
        )
        self.assertTrue(verdict.eligible)
        self.assertIn("contribution_type:workflow", verdict.signals)

    def test_capability_deferred_until_proven(self):
        receipt = {
            "receipt_sig": "signed",
            "invariants_passed": [{"status": "pass"}],
        }
        verdict = evaluate_pod_admission(
            operator_id="operator:helper",
            contribution_type="capability",
            receipt=receipt,
            receipt_verified=True,
        )
        self.assertFalse(verdict.eligible)
        self.assertEqual(verdict.reason, "deferred_until_proven:capability")

    def test_deferred_type_admits_when_proven_and_admit_on_proven_disabled(self):
        from src.ugr.discovery.proven_contribution import is_proven_contribution

        receipt = {
            "payload": {"claim_label": "proven"},
            "receipt_sig": "signed",
            "invariants_passed": [{"status": "pass", "details": "proven"}],
        }
        self.assertTrue(is_proven_contribution(receipt))
        policy = load_pod_admission_policy()
        policy = dict(policy)
        policy["admit_on_proven"] = False
        verdict = evaluate_pod_admission(
            operator_id="operator:cap-proven",
            contribution_type="capability",
            receipt=receipt,
            receipt_verified=True,
            policy=policy,
        )
        self.assertTrue(verdict.eligible)
        self.assertEqual(verdict.reason, "deferred_type_proven:capability")

    def test_explicit_pod_requires_receipt_when_flag_set(self):
        os.environ["UGR_POD_EXPLICIT_REQUIRES_RECEIPT"] = "1"
        verdict = evaluate_pod_admission(
            operator_id="operator:random-user",
            contribution_type="capability",
            spec_payload={"pod_display_name": "Random User"},
        )
        self.assertFalse(verdict.eligible)
        self.assertEqual(verdict.reason, "explicit_pod_requires_receipt")
        os.environ.pop("UGR_POD_EXPLICIT_REQUIRES_RECEIPT", None)

    def test_admission_metrics_increment_on_skip_and_admit(self):
        from src.ugr.discovery.pod_admission_metrics import reset_counters, snapshot_counters

        reset_counters()
        ledger_path = self.temp_root / "metrics-pods.jsonl"
        registry_path = self.temp_root / "metrics-pods.json"
        ledger = DiscoveryPodLedger(ledger_path=ledger_path, registry_path=registry_path)
        ledger.record_discovery(
            operator_id="op-1",
            tenant_id="tenant:acme",
            contribution_id="contrib-skip",
            contribution_type="workflow",
            spec_payload={},
            receipt_id="receipt-skip",
        )
        counters = snapshot_counters()
        self.assertGreaterEqual(counters["skip_total"], 1)
        self.assertGreaterEqual(counters["by_reason"].get("skip:insufficient_invariant_passes", 0), 1)

        reset_counters()
        receipt = {
            "receipt_sig": "signed",
            "invariants_passed": [{"status": "pass"}],
        }
        ledger.record_discovery(
            operator_id="operator:grace-hopper",
            tenant_id="global",
            contribution_id="contrib-admit",
            contribution_type="workflow",
            spec_payload={},
            receipt_id="receipt-admit",
            receipt=receipt,
            receipt_verified=True,
        )
        counters = snapshot_counters()
        self.assertGreaterEqual(counters["admit_total"], 1)
        reset_counters()

    def test_denies_system_operators(self):
        verdict = evaluate_pod_admission(
            operator_id="operator:system",
            contribution_type="proof",
            receipt={"receipt_sig": "x", "invariants_passed": [{"status": "pass"}]},
            receipt_verified=True,
            operator_slug="system",
        )
        self.assertFalse(verdict.eligible)
        self.assertTrue(verdict.reason.startswith("operator_slug_denied"))

    def test_skips_new_pod_when_not_worthy(self):
        ledger_path = self.temp_root / "pods.jsonl"
        registry_path = self.temp_root / "pods.json"
        ledger = DiscoveryPodLedger(ledger_path=ledger_path, registry_path=registry_path)
        result = ledger.record_discovery(
            operator_id="op-1",
            tenant_id="tenant:acme",
            contribution_id="contrib-low",
            contribution_type="workflow",
            spec_payload={},
            receipt_id="receipt-low",
        )
        self.assertTrue(result.ok)
        self.assertTrue(result.skipped)
        self.assertEqual(result.skip_reason, "insufficient_invariant_passes")
        self.assertEqual(len(ledger.list_pods()), 0)

    def test_admits_workflow_with_signed_receipt(self):
        ledger_path = self.temp_root / "pods2.jsonl"
        registry_path = self.temp_root / "pods2.json"
        ledger = DiscoveryPodLedger(ledger_path=ledger_path, registry_path=registry_path)
        receipt = {
            "receipt_sig": "signed",
            "invariants_passed": [{"status": "pass"}],
        }
        result = ledger.record_discovery(
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
        self.assertEqual(len(ledger.list_pods()), 1)

    def test_load_policy_overrides_list_fields(self):
        self.policy_path.write_text(
            json.dumps({"admit_contribution_types": ["proof"]}),
            encoding="utf-8",
        )
        policy = load_pod_admission_policy()
        self.assertEqual(policy["admit_contribution_types"], ["proof"])
        self.assertTrue(policy.get("admit_on_proven"))

    def test_env_overrides_min_invariant_pass_count(self):
        os.environ["UGR_POD_MIN_INVARIANT_PASS_COUNT"] = "0"
        self.assertEqual(min_invariant_pass_count_from_policy(load_pod_admission_policy()), 0)
        receipt = {"receipt_sig": "signed", "invariants_passed": []}
        verdict = evaluate_pod_admission(
            operator_id="operator:ada-lovelace",
            contribution_type="workflow",
            receipt=receipt,
            receipt_verified=True,
        )
        self.assertTrue(verdict.eligible)
        os.environ.pop("UGR_POD_MIN_INVARIANT_PASS_COUNT", None)

    def test_subsystem_discover_includes_pod_ledger(self):
        ledger_path = self.temp_root / "ledger" / "discovery-pods.jsonl"
        registry_path = self.temp_root / "ledger" / "discovery-pods.json"
        runtime = self.temp_root / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        os.environ["AAIS_RUNTIME_DIR"] = str(runtime)
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-subsystem-pod-key"
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "1"
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "1"
        os.environ["UGR_DISCOVERY_POD_LEDGER_PATH"] = str(ledger_path)
        os.environ["UGR_DISCOVERY_POD_REGISTRY_PATH"] = str(registry_path)
        try:
            discovery = SubsystemDiscoveryService(runtime_dir=str(runtime))
            result = discovery.discover(
                {
                    "tenant_id": "tenant:acme",
                    "operator_id": "operator:subsystem-pod-test",
                    "aais_instance_id": "aais-test-1",
                    "spec": {
                        "role": "llm_executor",
                        "io_shape": {"inputs": ["text"], "outputs": ["text"]},
                        "rail_class": "NORMAL",
                        "risk_ceiling": "low",
                        "tenant_class": "standard",
                    },
                }
            )
            self.assertEqual(result.get("status"), "discovered")
            pod_ledger = result.get("discovery_pod_ledger") or {}
            self.assertTrue(pod_ledger.get("ok"))
            self.assertFalse(pod_ledger.get("skipped"))
            self.assertEqual(pod_ledger.get("pod_id"), "pod:subsystem-pod-test")
            self.assertTrue(ledger_path.exists())
        finally:
            for key in (
                "AAIS_RUNTIME_DIR",
                "URG_RECEIPT_SIGNING_KEY",
                "UGR_SUBSYSTEM_DISCOVERY_ENABLED",
                "UGR_REWARDS_SHADOW_ONLY",
                "UGR_DISCOVERY_POD_LEDGER_PATH",
                "UGR_DISCOVERY_POD_REGISTRY_PATH",
            ):
                os.environ.pop(key, None)


if __name__ == "__main__":
    unittest.main()
