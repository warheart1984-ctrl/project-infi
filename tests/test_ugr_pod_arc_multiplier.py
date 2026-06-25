"""Tests for governance-arc pod reward multipliers."""

import json
import os
import unittest

from src.ugr.discovery.pod_arc_multiplier import (
    TIER_BEYOND_BODY,
    TIER_CIVILIZATIONAL,
    TIER_LOW,
    TIER_MED,
    TIER_MED_HIGH,
    apply_pod_arc_multiplier_to_deltas,
    arc_multipliers_from_policy,
    resolve_pod_arc_context,
)
from src.ugr.rewards.operator_profile import OperatorProfile
from src.ugr.rewards.operator_reward_spec import EVENT_PROOF_PACKET_PUBLISHED
from src.ugr.rewards.reward_calculator import compute_deltas


class TestPodArcMultiplier(unittest.TestCase):
    def tearDown(self):
        for key in (
            "UGR_POD_ARC_MULTIPLIER",
            "UGR_POD_ARC_MULTIPLIER_LOW",
            "UGR_POD_ARC_MULTIPLIER_MED",
            "UGR_POD_ARC_MULTIPLIER_MED_HIGH",
            "UGR_POD_ARC_MULTIPLIER_HIGH",
            "UGR_POD_ARC_MULTIPLIER_CIVILIZATIONAL",
        ):
            os.environ.pop(key, None)

    def test_high_arc_tier_from_governance_arc(self):
        ctx = resolve_pod_arc_context(spec_payload={"governance_arc": "high"})
        self.assertEqual(ctx.tier, TIER_BEYOND_BODY)
        self.assertEqual(ctx.multiplier, 10.0)

    def test_civilizational_arc_from_batch_id(self):
        ctx = resolve_pod_arc_context(
            spec_payload={
                "activation": {"batch_id": "civilizational-arc-stage15-2026-06"},
            }
        )
        self.assertEqual(ctx.tier, TIER_CIVILIZATIONAL)
        self.assertEqual(ctx.multiplier, 10.0)

    def test_beyond_body_from_anatomical_layer(self):
        ctx = resolve_pod_arc_context(spec_payload={"anatomical_layer": 15})
        self.assertEqual(ctx.tier, TIER_BEYOND_BODY)
        self.assertEqual(ctx.multiplier, 10.0)

    def test_apply_multiplier_scales_reputation_and_rail_credits(self):
        ctx = resolve_pod_arc_context(spec_payload={"governance_arc": "civilizational"})
        scaled = apply_pod_arc_multiplier_to_deltas(
            {"reputation": 18.0, "rail_credits": 2.0, "earned_rail_credits": 2.0},
            multiplier=ctx.multiplier,
            arc_context=ctx,
        )
        self.assertEqual(scaled["reputation"], 180.0)
        self.assertEqual(scaled["rail_credits"], 20.0)
        self.assertEqual(scaled["pod_reward_multiplier"], 10.0)
        self.assertEqual(scaled["governance_arc_tier"], TIER_CIVILIZATIONAL)

    def test_compute_deltas_applies_10x_for_civilizational_proof(self):
        profile = OperatorProfile(
            operator_id="operator:arc-tester",
            tenant_id="tenant:default",
            reputation_score=0.0,
        )
        receipt = {
            "payload": {
                "claim_label": "proven",
                "governance_arc": "civilizational",
            }
        }
        deltas = compute_deltas(EVENT_PROOF_PACKET_PUBLISHED, receipt, profile)
        self.assertIsNotNone(deltas)
        self.assertEqual(deltas["reputation"], 580.0)
        self.assertEqual(deltas["pod_reward_multiplier"], 10.0)
        self.assertEqual(deltas["governance_arc_tier"], TIER_CIVILIZATIONAL)

    def test_env_override_high_multiplier(self):
        os.environ["UGR_POD_ARC_MULTIPLIER_HIGH"] = "5"
        ctx = resolve_pod_arc_context(spec_payload={"governance_arc": "high"})
        self.assertEqual(ctx.multiplier, 5.0)

    def test_graduated_arc_tiers_from_policy(self):
        multipliers = arc_multipliers_from_policy()
        self.assertEqual(multipliers[TIER_LOW], 2.0)
        self.assertEqual(multipliers[TIER_MED], 4.0)
        self.assertEqual(multipliers[TIER_MED_HIGH], 7.0)
        self.assertEqual(multipliers[TIER_BEYOND_BODY], 10.0)
        self.assertEqual(multipliers[TIER_CIVILIZATIONAL], 10.0)

    def test_low_med_med_high_governance_arc_labels(self):
        low = resolve_pod_arc_context(spec_payload={"governance_arc": "low"})
        med = resolve_pod_arc_context(spec_payload={"governance_arc": "med"})
        med_high = resolve_pod_arc_context(spec_payload={"governance_arc": "med-high"})
        self.assertEqual(low.tier, TIER_LOW)
        self.assertEqual(low.multiplier, 2.0)
        self.assertEqual(med.tier, TIER_MED)
        self.assertEqual(med.multiplier, 4.0)
        self.assertEqual(med_high.tier, TIER_MED_HIGH)
        self.assertEqual(med_high.multiplier, 7.0)

    def test_anatomical_layer_graduated_tiers(self):
        layer_9 = resolve_pod_arc_context(spec_payload={"anatomical_layer": 9})
        layer_12 = resolve_pod_arc_context(spec_payload={"anatomical_layer": 12})
        layer_13 = resolve_pod_arc_context(spec_payload={"anatomical_layer": 13})
        self.assertEqual(layer_9.tier, TIER_LOW)
        self.assertEqual(layer_12.tier, TIER_MED)
        self.assertEqual(layer_13.tier, TIER_MED_HIGH)

    def test_apply_graduated_multiplier_to_deltas(self):
        ctx = resolve_pod_arc_context(spec_payload={"governance_arc": "med"})
        scaled = apply_pod_arc_multiplier_to_deltas(
            {"reputation": 18.0, "rail_credits": 2.0, "earned_rail_credits": 2.0},
            multiplier=ctx.multiplier,
            arc_context=ctx,
        )
        self.assertEqual(scaled["reputation"], 72.0)
        self.assertEqual(scaled["rail_credits"], 8.0)
        self.assertEqual(scaled["pod_reward_multiplier"], 4.0)
        self.assertEqual(scaled["governance_arc_tier"], TIER_MED)


class TestPodArcReactivation(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile
        from pathlib import Path

        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-pod-arc-react-"))
        self.ledger_path = self.temp_root / "pods.jsonl"
        self.registry_path = self.temp_root / "pods-registry.json"
        self.rewards_path = self.temp_root / "rewards.jsonl"
        self.balances_dir = self.temp_root / "operators" / "operator_arc-tester"
        self.balances_dir.mkdir(parents=True)
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["UGR_DISCOVERY_POD_LEDGER_PATH"] = str(self.ledger_path)
        os.environ["UGR_DISCOVERY_POD_REGISTRY_PATH"] = str(self.registry_path)

        pod_seed = {
            "event_id": "pod-seed",
            "event_type": "pod_registered",
            "ledger_id": "ugr.discovery.pods",
            "ledger_version": "1.0",
            "recorded_at_utc": "2026-06-07T00:00:00Z",
            "pod_index": 1,
            "pod_id": "pod:arc-tester",
            "display_name": "Arc Tester",
            "operator_id": "operator:arc-tester",
            "status": "active",
        }
        pod_proven = {
            "event_id": "pprov-test",
            "event_type": "pod_proven",
            "ledger_id": "ugr.discovery.pods",
            "ledger_version": "1.0",
            "recorded_at_utc": "2026-06-07T01:00:00Z",
            "pod_id": "pod:arc-tester",
            "operator_id": "operator:arc-tester",
            "tenant_id": "global",
            "contribution_id": "contrib-abc",
            "receipt_id": "receipt-1",
            "reputation_awarded": 18.0,
            "rail_credits_awarded": 2.0,
            "reward_event_id": "reward-base",
            "reward_status": "issued",
        }
        self.ledger_path.write_text(
            json.dumps(pod_seed) + "\n" + json.dumps(pod_proven) + "\n",
            encoding="utf-8",
        )
        reward_event = {
            "event_id": "reward-base",
            "event_type": "proof_packet_published",
            "operator_id": "operator:arc-tester",
            "tenant_id": "global",
            "contribution_id": "contrib-abc",
            "status": "issued",
            "deltas": {"reputation": 18.0, "rail_credits": 2.0, "earned_rail_credits": 2.0},
        }
        self.rewards_path.write_text(json.dumps(reward_event) + "\n", encoding="utf-8")
        (self.balances_dir / "operator_balances.json").write_text(
            json.dumps(
                {
                    "operator_id": "operator:arc-tester",
                    "tenant_id": "global",
                    "reputation_score": 18.0,
                    "earned_rail_credits": 2.0,
                    "rail_credits": 2.0,
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        import shutil

        for key in ("AAIS_RUNTIME_DIR", "UGR_DISCOVERY_POD_LEDGER_PATH", "UGR_DISCOVERY_POD_REGISTRY_PATH"):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_reactivate_applies_10x_adjustment(self):
        import json
        from pathlib import Path

        from src.ugr.discovery.pod_arc_reactivation import reactivate_pod_arc_multiplier
        from src.ugr.rewards.reward_ledger import RewardLedger

        runtime = Path(os.environ["AAIS_RUNTIME_DIR"])
        tenant_rewards = runtime / "urg" / "rewards" / "global" / "rewards.jsonl"
        tenant_rewards.parent.mkdir(parents=True, exist_ok=True)
        tenant_rewards.write_text(self.rewards_path.read_text(encoding="utf-8"), encoding="utf-8")
        op_dir = runtime / "urg" / "rewards" / "global" / "operators" / "operator_arc-tester"
        op_dir.mkdir(parents=True, exist_ok=True)
        (op_dir / "operator_balances.json").write_text(
            (self.balances_dir / "operator_balances.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        result = reactivate_pod_arc_multiplier(
            pod_id="pod:arc-tester",
            arc_tier="civilizational",
            runtime_dir=str(runtime),
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("reputation_adjustment"), 162.0)
        self.assertEqual(result.get("rail_credits_adjustment"), 18.0)

        ledger = RewardLedger(runtime_dir=str(runtime), tenant_id="global")
        profile = ledger.load_balances("operator:arc-tester")
        self.assertEqual(profile.reputation_score, 180.0)
        self.assertEqual(profile.earned_rail_credits, 20.0)

        again = reactivate_pod_arc_multiplier(
            pod_id="pod:arc-tester",
            arc_tier="civilizational",
            runtime_dir=str(runtime),
        )
        self.assertTrue(again.get("skipped"))
        self.assertTrue(again.get("idempotent"))

    def test_newer_proven_event_controls_last_reputation_after_arc_reactivation(self):
        from src.ugr.discovery.discovery_pod_ledger import DiscoveryPodLedger

        rows = [
            {
                "event_id": "pod-seed",
                "event_type": "pod_registered",
                "recorded_at_utc": "2026-06-07T00:00:00Z",
                "pod_index": 1,
                "pod_id": "pod:arc-tester",
                "display_name": "Arc Tester",
                "operator_id": "operator:arc-tester",
                "status": "active",
            },
            {
                "event_id": "pprov-base",
                "event_type": "pod_proven",
                "recorded_at_utc": "2026-06-07T01:00:00Z",
                "pod_id": "pod:arc-tester",
                "operator_id": "operator:arc-tester",
                "contribution_id": "contrib-base",
                "reputation_awarded": 18.0,
                "rail_credits_awarded": 2.0,
                "reward_status": "issued",
            },
            {
                "event_id": "parc-base",
                "event_type": "pod_arc_reactivated",
                "recorded_at_utc": "2026-06-07T02:00:00Z",
                "pod_id": "pod:arc-tester",
                "operator_id": "operator:arc-tester",
                "contribution_id": "contrib-base",
                "reputation_adjustment": 162.0,
                "reputation_awarded": 180.0,
                "rail_credits_adjustment": 18.0,
                "rail_credits_awarded": 20.0,
                "pod_reward_multiplier": 10.0,
            },
            {
                "event_id": "pprov-new",
                "event_type": "pod_proven",
                "recorded_at_utc": "2026-06-08T01:00:00Z",
                "pod_id": "pod:arc-tester",
                "operator_id": "operator:arc-tester",
                "contribution_id": "contrib-new",
                "reputation_awarded": 580.0,
                "rail_credits_awarded": 100.0,
                "reward_status": "issued",
            },
        ]
        self.ledger_path.write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n",
            encoding="utf-8",
        )

        stats = DiscoveryPodLedger().proven_stats("pod:arc-tester")

        self.assertEqual(stats["proven_count"], 2)
        self.assertEqual(stats["total_reputation_awarded"], 760.0)
        self.assertEqual(stats["last_proven_contribution_id"], "contrib-new")
        self.assertEqual(stats["last_reputation_awarded"], 580.0)


class TestPodArcRelabel(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path

        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-pod-arc-relabel-"))
        self.ledger_path = self.temp_root / "pods.jsonl"
        self.registry_path = self.temp_root / "pods-registry.json"
        os.environ["UGR_DISCOVERY_POD_LEDGER_PATH"] = str(self.ledger_path)
        os.environ["UGR_DISCOVERY_POD_REGISTRY_PATH"] = str(self.registry_path)

        rows = [
            {
                "event_id": "pod-seed",
                "event_type": "pod_registered",
                "ledger_id": "ugr.discovery.pods",
                "ledger_version": "1.0",
                "recorded_at_utc": "2026-06-07T00:00:00Z",
                "pod_index": 1,
                "pod_id": "pod:relabel-tester",
                "display_name": "Relabel Tester",
                "operator_id": "operator:relabel-tester",
                "status": "active",
            },
            {
                "event_id": "pprov-relabel",
                "event_type": "pod_proven",
                "ledger_id": "ugr.discovery.pods",
                "ledger_version": "1.0",
                "recorded_at_utc": "2026-06-07T01:00:00Z",
                "pod_id": "pod:relabel-tester",
                "operator_id": "operator:relabel-tester",
                "contribution_id": "contrib-relabel",
                "reputation_awarded": 180.0,
                "governance_arc_tier": TIER_CIVILIZATIONAL,
                "pod_reward_multiplier": 10.0,
            },
            {
                "event_id": "parc-relabel",
                "event_type": "pod_arc_reactivated",
                "ledger_id": "ugr.discovery.pods",
                "ledger_version": "1.0",
                "recorded_at_utc": "2026-06-07T02:00:00Z",
                "pod_id": "pod:relabel-tester",
                "operator_id": "operator:relabel-tester",
                "contribution_id": "contrib-relabel",
                "governance_arc_tier": TIER_CIVILIZATIONAL,
                "pod_reward_multiplier": 10.0,
                "reputation_adjustment": 162.0,
            },
        ]
        self.ledger_path.write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n",
            encoding="utf-8",
        )

    def tearDown(self):
        import shutil

        for key in ("UGR_DISCOVERY_POD_LEDGER_PATH", "UGR_DISCOVERY_POD_REGISTRY_PATH"):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_relabel_updates_display_tier_without_economic_change(self):
        from src.ugr.discovery.discovery_pod_ledger import DiscoveryPodLedger
        from src.ugr.discovery.pod_arc_relabel import relabel_pod_arc_tier

        ledger = DiscoveryPodLedger()
        before = ledger.arc_stats("pod:relabel-tester")
        self.assertEqual(before["governance_arc_tier"], TIER_CIVILIZATIONAL)
        self.assertEqual(before["pod_reward_multiplier"], 10.0)

        result = relabel_pod_arc_tier(
            pod_id="pod:relabel-tester",
            arc_tier="high",
            narrative_note="Founding proof was Beyond the Body",
            ledger=ledger,
        )
        self.assertTrue(result.get("ok"))
        self.assertFalse(result.get("skipped"))
        self.assertEqual(result["governance_arc_tier"], TIER_BEYOND_BODY)
        self.assertEqual(result["previous_governance_arc_tier"], TIER_CIVILIZATIONAL)
        self.assertEqual(result["pod_reward_multiplier"], 10.0)
        self.assertTrue(result.get("narrative_only"))

        after = ledger.arc_stats("pod:relabel-tester")
        self.assertEqual(after["governance_arc_tier"], TIER_BEYOND_BODY)
        self.assertEqual(after["pod_reward_multiplier"], 10.0)
        self.assertEqual(after.get("governance_arc_tier_economic"), TIER_CIVILIZATIONAL)

        registry = ledger.build_registry()
        pod = registry["pods"]["pod:relabel-tester"]
        self.assertEqual(pod["governance_arc_tier"], TIER_BEYOND_BODY)
        self.assertEqual(pod["pod_reward_multiplier"], 10.0)

        again = relabel_pod_arc_tier(
            pod_id="pod:relabel-tester",
            arc_tier="high",
            narrative_note="Founding proof was Beyond the Body",
            ledger=ledger,
        )
        self.assertTrue(again.get("skipped"))
        self.assertTrue(again.get("idempotent"))


if __name__ == "__main__":
    unittest.main()
