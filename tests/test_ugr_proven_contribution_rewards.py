"""Proven contributions auto-persist operator rewards and upgrade pod ledger."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.proven_contribution import is_proven_contribution, is_standing_proven
from src.ugr.rewards.operator_reward_engine import OperatorRewardEngine
from src.ugr.rewards.reward_ledger import RewardLedger, _operator_slug


class TestProvenContributionRewards(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-proven-rewards-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-proven-reward-key"
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "1"
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "1"
        os.environ["UGR_REWARDS_PROVEN_PERSIST"] = "1"
        self.proof_path = self.temp_root / "proof.md"
        self.proof_path.write_text("# Proven test packet\n", encoding="utf-8")
        self.ledger_path = self.temp_root / "pods.jsonl"
        self.registry_path = self.temp_root / "pods-registry.json"
        os.environ["UGR_DISCOVERY_POD_LEDGER_PATH"] = str(self.ledger_path)
        os.environ["UGR_DISCOVERY_POD_REGISTRY_PATH"] = str(self.registry_path)

    def tearDown(self):
        for key in (
            "AAIS_RUNTIME_DIR",
            "URG_RECEIPT_SIGNING_KEY",
            "UGR_SUBSYSTEM_DISCOVERY_ENABLED",
            "UGR_REWARDS_SHADOW_ONLY",
            "UGR_REWARDS_PROVEN_PERSIST",
            "UGR_DISCOVERY_POD_LEDGER_PATH",
            "UGR_DISCOVERY_POD_REGISTRY_PATH",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _discover_proof(self, *, run_id: str = "1") -> dict:
        service = ContributionDiscoveryService(runtime_dir=str(self.temp_root))
        return service.discover(
            {
                "tenant_id": "global",
                "operator_id": "operator:proven-tester",
                "aais_instance_id": "aais-test",
                "contribution_type": "proof",
                "payload": {
                    "proof_path": str(self.proof_path),
                    "claim_label": "proven",
                    "discovery_pod_id": "pod:proven-tester",
                    "run_id": run_id,
                },
            }
        )

    def test_is_proven_contribution_from_payload(self):
        receipt = {
            "payload": {"claim_label": "proven", "standing": 3},
            "invariants_passed": [{"family": "repo_proof_law", "status": "pass", "details": "proven"}],
        }
        self.assertTrue(is_proven_contribution(receipt))
        self.assertTrue(is_standing_proven(receipt))
        self.assertFalse(is_proven_contribution({"payload": {"claim_label": "asserted", "standing": 2}}))

    def test_operator_slug_strips_colons_for_windows_paths(self):
        self.assertEqual(_operator_slug("operator:jon-halstead"), "operator_jon-halstead")

    def test_proven_discovery_persists_rewards_under_shadow_only(self):
        result = self._discover_proof()
        self.assertEqual(result.get("status"), "discovered")
        rewards = result.get("operator_rewards") or {}
        self.assertEqual(rewards.get("status"), "issued")
        profile = rewards.get("profile") or {}
        self.assertEqual(profile.get("reputation_score"), 58.0)

        ledger = RewardLedger(runtime_dir=str(self.temp_root), tenant_id="global")
        stored = ledger.load_balances("operator:proven-tester")
        self.assertEqual(stored.reputation_score, 58.0)
        self.assertTrue(ledger.tenant_rewards_path.exists())

    def test_proven_discovery_records_pod_proven_ledger(self):
        result = self._discover_proof(run_id="2")
        pod_ledger = result.get("discovery_pod_ledger") or {}
        proven = pod_ledger.get("pod_proven") or {}
        self.assertTrue(proven.get("ok"))
        self.assertEqual(proven.get("reputation_awarded"), 58.0)

        lines = [ln for ln in self.ledger_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        event_types = [json.loads(ln).get("event_type") for ln in lines]
        self.assertIn("pod_proven", event_types)

        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        pod = registry["pods"]["pod:proven-tester"]
        self.assertGreaterEqual(pod.get("proven_count"), 1)
        self.assertEqual(pod.get("total_reputation_awarded"), 58.0)

    def test_civilizational_arc_applies_10x_proven_rewards(self):
        service = ContributionDiscoveryService(runtime_dir=str(self.temp_root))
        result = service.discover(
            {
                "tenant_id": "global",
                "operator_id": "operator:civilizational-tester",
                "aais_instance_id": "aais-test",
                "contribution_type": "proof",
                "payload": {
                    "proof_path": str(self.proof_path),
                    "claim_label": "proven",
                    "governance_arc": "civilizational",
                    "discovery_pod_id": "pod:civilizational-tester",
                    "run_id": "civ-arc-1",
                },
            }
        )
        self.assertEqual(result.get("status"), "discovered")
        rewards = result.get("operator_rewards") or {}
        self.assertEqual(rewards.get("status"), "issued")
        profile = rewards.get("profile") or {}
        self.assertEqual(profile.get("reputation_score"), 580.0)
        deltas = rewards.get("deltas") or {}
        self.assertEqual(deltas.get("pod_reward_multiplier"), 10.0)
        self.assertEqual(deltas.get("governance_arc_tier"), "civilizational")

        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        pod = registry["pods"]["pod:civilizational-tester"]
        self.assertEqual(pod.get("governance_arc_tier"), "civilizational")
        self.assertEqual(pod.get("pod_reward_multiplier"), 10.0)
        self.assertEqual(pod.get("total_reputation_awarded"), 580.0)

    def test_idempotent_rediscovery_still_issues_proven_rewards_once(self):
        first = self._discover_proof(run_id="3a")
        self.assertEqual((first.get("operator_rewards") or {}).get("status"), "issued")

        second = self._discover_proof(run_id="3a")
        self.assertTrue(second.get("idempotent"))
        rewards = second.get("operator_rewards") or {}
        self.assertEqual(rewards.get("status"), "idempotent")

        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        profile = engine.get_profile("operator:proven-tester", tenant_id="global")
        self.assertEqual(profile.get("reputation_score"), 58.0)


if __name__ == "__main__":
    unittest.main()
