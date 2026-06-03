"""Tests for UGR Operator Rewards — governed cognitive economy."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ugr.cloud_forge_bridge import apply_rail_credit_boost_to_forge, schedule_rail_for_ugr
from src.ugr.discovery.subsystem_discovery import SubsystemDiscoveryService
from src.ugr.rewards.operator_reward_engine import OperatorRewardEngine, rewards_enabled
from src.ugr.rewards.operator_reward_receipt import verify_operator_reward_receipt
from src.ugr.rewards.rail_credit_spend import spend_rail_credits, validate_forge_boost


def _valid_spec() -> dict:
    return {
        "role": "llm_executor",
        "io_shape": {"inputs": ["text"], "outputs": ["text"]},
        "rail_class": "NORMAL",
        "risk_ceiling": "low",
        "tenant_class": "standard",
    }


class TestOperatorRewards(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-rewards-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "test-rewards-op-key"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-rewards-urg-key"
        os.environ["UGR_OPERATOR_REWARDS_ENABLED"] = "1"
        os.environ["UGR_RAIL_CREDIT_SPEND_ENABLED"] = "1"
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "1"

    def tearDown(self):
        for key in (
            "AAIS_RUNTIME_DIR",
            "URG_OPERATOR_RECEIPT_KEY",
            "URG_RECEIPT_SIGNING_KEY",
            "UGR_OPERATOR_REWARDS_ENABLED",
            "UGR_RAIL_CREDIT_SPEND_ENABLED",
            "UGR_SUBSYSTEM_DISCOVERY_ENABLED",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_discovery_emits_rewards_once(self):
        discovery = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        payload = {
            "tenant_id": "tenant:acme",
            "operator_id": "op-rewards",
            "aais_instance_id": "aais-test-1",
            "spec": _valid_spec(),
        }
        first = discovery.discover(payload)
        self.assertEqual(first.get("status"), "discovered")
        rewards = first.get("operator_rewards") or {}
        self.assertEqual(rewards.get("status"), "issued")
        receipt = rewards.get("operator_reward_receipt") or {}
        ok, _ = verify_operator_reward_receipt(receipt, runtime_dir=str(self.temp_root))
        self.assertTrue(ok)

        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        profile = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        self.assertGreaterEqual(profile.get("reputation_score", 0), 15)
        self.assertGreaterEqual(profile.get("rail_credits", 0), 3)
        self.assertGreaterEqual(
            profile.get("reputation_score", 0),
            profile.get("rail_credits", 0) * 2,
            "reputation must dominate rail credits",
        )
        attribution = (rewards.get("attribution") or receipt.get("attribution") or {})
        self.assertIn("lifecycle_chain", attribution)

        second = discovery.discover(payload)
        self.assertTrue(second.get("idempotent"))
        idem_rewards = second.get("operator_rewards") or {}
        self.assertEqual(idem_rewards.get("status"), "skipped")

        profile2 = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        self.assertEqual(profile2.get("reputation_score"), profile.get("reputation_score"))

    def test_spend_and_forge_boost(self):
        discovery = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        discovery.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-rewards",
                "aais_instance_id": "aais-test-1",
                "spec": _valid_spec(),
            }
        )
        spend = spend_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-rewards",
            amount=2,
            trace_id="trace-spend-1",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(spend.get("status"), "ok")
        boost = spend.get("forge_boost") or {}
        ok, reason, _ = validate_forge_boost(boost, runtime_dir=str(self.temp_root))
        self.assertTrue(ok, reason)

        profile_before = {"wL_express_threshold": 100.0, "wL_express_floor": 50.0}
        actor_before = {"wL": 100.0}
        request = {
            "context": {"rail_credit_boost": boost},
            "tenant_id": "tenant:acme",
            "operator_id": "op-rewards",
        }
        profile_after, actor_after, meta = apply_rail_credit_boost_to_forge(
            request,
            profile_before,
            actor_before,
            runtime_dir=str(self.temp_root),
        )
        self.assertTrue(meta.get("rail_credit_boost", {}).get("applied"))
        self.assertLess(profile_after["wL_express_threshold"], profile_before["wL_express_threshold"])
        self.assertGreater(actor_after["wL"], actor_before["wL"])

        ok2, reason2, _ = validate_forge_boost(boost, runtime_dir=str(self.temp_root))
        self.assertFalse(ok2)
        self.assertIn("consumed", reason2)

    def test_schedule_rail_applies_boost(self):
        discovery = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        discovery.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-rewards",
                "aais_instance_id": "aais-test-1",
                "spec": _valid_spec(),
            }
        )
        spend = spend_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-rewards",
            amount=1,
            trace_id="trace-spend-2",
            runtime_dir=str(self.temp_root),
        )
        boost = spend.get("forge_boost") or {}
        request = {
            "question": "probe express boost",
            "intent": "general_qa",
            "tenant_id": "tenant:acme",
            "operator_id": "op-rewards",
            "context": {"rail_credit_boost": boost, "mutation_scope": "read"},
        }
        with patch.dict(os.environ, {"AAIS_RUNTIME_DIR": str(self.temp_root)}):
            bundle = schedule_rail_for_ugr(request, trace_id="boost-trace-1")
        self.assertIsNotNone(bundle)
        boost_meta = (bundle or {}).get("rail_credit_boost") or {}
        self.assertTrue(boost_meta.get("applied"), boost_meta)

    def test_rewards_disabled(self):
        os.environ["UGR_OPERATOR_REWARDS_ENABLED"] = "0"
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        result = engine.emit_for_discovery(
            {
                "receipt_id": "x",
                "subsystem_id": "a" * 64,
                "operator_id": "op-rewards",
                "tenant_id": "tenant:acme",
            }
        )
        self.assertEqual(result.get("status"), "disabled")

    def test_tenant_isolation(self):
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        engine._emit(
            event_type="subsystem_discovered",
            operator_id="op-a",
            tenant_id="tenant:acme",
            subsystem_id="b" * 64,
            discovery_receipt_id="receipt-a",
            reputation=1,
            rail_credits=1,
        )
        profile = engine.get_profile("op-a", tenant_id="tenant:contoso")
        self.assertEqual(profile.get("reputation_score"), 0)

    def test_promotion_rewards_blocked_without_ok(self):
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        receipt = {
            "receipt_id": "r1",
            "subsystem_id": "c" * 64,
            "operator_id": "op-rewards",
            "tenant_id": "tenant:acme",
        }
        result = engine.emit_for_promotion(
            receipt,
            governance_mission_id="mid-1",
            promotion_organ_id="discovered-foo",
            governance_status="blocked",
        )
        self.assertEqual(result.get("status"), "skipped")

    def test_rewards_enabled_default(self):
        os.environ.pop("UGR_OPERATOR_REWARDS_ENABLED", None)
        self.assertTrue(rewards_enabled())

    def test_spend_blocked_without_reputation_standing(self):
        spend = spend_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-new",
            amount=1,
            trace_id="trace-low-rep",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(spend.get("status"), "rejected")
        self.assertIn("reputation", str(spend.get("summary") or "").lower())

    def test_reputation_primary_credit_cap(self):
        from src.ugr.rewards.reward_policy import cap_rail_credit_earn

        capped = cap_rail_credit_earn(15, 100, profile_reputation=0)
        self.assertLessEqual(capped, 15 / 2)
        self.assertGreater(capped, 0)


if __name__ == "__main__":
    unittest.main()
