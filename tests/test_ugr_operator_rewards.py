"""Tests for UGR Operator Rewards — governed cognitive economy + discovery receipt gate."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ugr.cloud_forge_bridge import apply_rail_credit_boost_to_forge, schedule_rail_for_ugr
from src.ugr.discovery.subsystem_discovery import SubsystemDiscoveryService
from src.ugr.discovery.subsystem_discovery_store import SubsystemDiscoveryStore
from src.ugr.rewards.operator_reward_engine import OperatorRewardEngine, rewards_enabled
from src.ugr.rewards.operator_reward_receipt import verify_operator_reward_receipt
from src.ugr.rewards.operator_reward_spec import EVENT_SUBSYSTEM_DISCOVERED, EVENT_SUBSYSTEM_PROMOTED
from src.ugr.rewards.operator_credit_transfer_receipt import verify_credit_transfer_receipt
from src.ugr.rewards.rail_credit_spend import spend_rail_credits, validate_forge_boost
from src.ugr.rewards.rail_credit_transfer import exchange_rail_credits, transfer_rail_credits
from src.ugr.rewards.reward_issuer import issue_reward
from src.ugr.rewards.reward_ledger import RewardLedger


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
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "0"
        os.environ["UGR_REWARDS_AUDIT_ONLY"] = "0"
        os.environ["UGR_RAIL_CREDIT_TRANSFER_ENABLED"] = "1"

    def tearDown(self):
        for key in (
            "AAIS_RUNTIME_DIR",
            "URG_OPERATOR_RECEIPT_KEY",
            "URG_RECEIPT_SIGNING_KEY",
            "UGR_OPERATOR_REWARDS_ENABLED",
            "UGR_RAIL_CREDIT_SPEND_ENABLED",
            "UGR_SUBSYSTEM_DISCOVERY_ENABLED",
            "UGR_REWARDS_SHADOW_ONLY",
            "UGR_REWARDS_AUDIT_ONLY",
            "UGR_RAIL_CREDIT_TRANSFER_ENABLED",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _discover(self) -> dict:
        discovery = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        return discovery.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-rewards",
                "aais_instance_id": "aais-test-1",
                "spec": _valid_spec(),
            }
        )

    def test_discovery_emits_rewards_once(self):
        first = self._discover()
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

        discovery = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        second = discovery.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-rewards",
                "aais_instance_id": "aais-test-1",
                "spec": _valid_spec(),
            }
        )
        self.assertTrue(second.get("idempotent"))
        idem_rewards = second.get("operator_rewards") or {}
        self.assertEqual(idem_rewards.get("status"), "skipped")

        profile2 = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        self.assertEqual(profile2.get("reputation_score"), profile.get("reputation_score"))

    def test_gate_unknown_subsystem_rejected(self):
        result = issue_reward(
            tenant_id="tenant:acme",
            operator_id="op-rewards",
            subsystem_id="f" * 64,
            event_type=EVENT_SUBSYSTEM_DISCOVERED,
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "rejected")
        self.assertEqual(result.get("reason"), "discovery_receipt_unresolved")
        profile = OperatorRewardEngine(runtime_dir=str(self.temp_root)).get_profile(
            "op-rewards", tenant_id="tenant:acme"
        )
        self.assertEqual(profile.get("reputation_score"), 0)

    def test_gate_wrong_discovery_receipt_id_rejected(self):
        first = self._discover()
        subsystem_id = str((first.get("subsystem_discovery_receipt") or {}).get("subsystem_id") or "")
        result = issue_reward(
            tenant_id="tenant:acme",
            operator_id="op-rewards",
            subsystem_id=subsystem_id,
            event_type=EVENT_SUBSYSTEM_DISCOVERED,
            discovery_receipt_id="wrong-receipt-id",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "rejected")
        self.assertEqual(result.get("reason"), "discovery_receipt_unresolved")

    def test_gate_tampered_receipt_rejected(self):
        first = self._discover()
        subsystem_id = str((first.get("subsystem_discovery_receipt") or {}).get("subsystem_id") or "")
        store = SubsystemDiscoveryStore(runtime_dir=str(self.temp_root), tenant_id="tenant:acme")
        receipt = store.get_by_subsystem_id(subsystem_id)
        self.assertIsNotNone(receipt)
        tampered = dict(receipt)
        tampered["operator_id"] = "attacker"
        tampered["receipt_signature"] = "invalid-signature"
        with store.discoveries_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "subsystem_id": subsystem_id,
                        "receipt_id": receipt.get("receipt_id"),
                        "tenant_id": "tenant:acme",
                        "receipt": tampered,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        result = issue_reward(
            tenant_id="tenant:acme",
            operator_id="op-rewards",
            subsystem_id=subsystem_id,
            event_type=EVENT_SUBSYSTEM_PROMOTED,
            governance_mission_id="mid-1",
            promotion_organ_id="discovered-foo",
            governance_status="ok",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "rejected")
        self.assertEqual(result.get("reason"), "discovery_receipt_unresolved")

    def test_audit_only_no_ledger_write(self):
        os.environ["UGR_REWARDS_AUDIT_ONLY"] = "1"
        first = self._discover()
        subsystem_id = str((first.get("subsystem_discovery_receipt") or {}).get("subsystem_id") or "")
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        profile_before = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        result = issue_reward(
            tenant_id="tenant:acme",
            operator_id="op-rewards",
            subsystem_id=subsystem_id,
            event_type=EVENT_SUBSYSTEM_PROMOTED,
            governance_mission_id="mid-audit",
            promotion_organ_id="discovered-audit",
            governance_status="ok",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "audit")
        self.assertIn("deltas", result)
        profile_after = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        self.assertEqual(profile_after.get("reputation_score"), profile_before.get("reputation_score"))
        events = engine.list_ledger(tenant_id="tenant:acme", subsystem_id=subsystem_id)
        promo_events = [e for e in events if e.get("event_type") == EVENT_SUBSYSTEM_PROMOTED]
        self.assertEqual(len(promo_events), 0)

    def test_spend_and_forge_boost(self):
        self._discover()
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
        self._discover()
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
        first = self._discover()
        subsystem_id = str((first.get("subsystem_discovery_receipt") or {}).get("subsystem_id") or "")
        result = engine.issue(
            tenant_id="tenant:acme",
            operator_id="op-rewards",
            subsystem_id=subsystem_id,
            event_type=EVENT_SUBSYSTEM_DISCOVERED,
        )
        self.assertEqual(result.get("status"), "disabled")

    def test_tenant_isolation(self):
        first = self._discover()
        subsystem_id = str((first.get("subsystem_discovery_receipt") or {}).get("subsystem_id") or "")
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        profile_acme = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        self.assertGreater(profile_acme.get("reputation_score", 0), 0)
        profile_contoso = engine.get_profile("op-rewards", tenant_id="tenant:contoso")
        self.assertEqual(profile_contoso.get("reputation_score"), 0)
        issue_reward(
            tenant_id="tenant:contoso",
            operator_id="op-rewards",
            subsystem_id=subsystem_id,
            event_type=EVENT_SUBSYSTEM_DISCOVERED,
            runtime_dir=str(self.temp_root),
        )
        profile_contoso2 = engine.get_profile("op-rewards", tenant_id="tenant:contoso")
        self.assertEqual(profile_contoso2.get("reputation_score"), 0)

    def test_promotion_rewards_blocked_without_ok(self):
        first = self._discover()
        subsystem_id = str((first.get("subsystem_discovery_receipt") or {}).get("subsystem_id") or "")
        receipt = (first.get("subsystem_discovery_receipt") or {})
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
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

    def test_transfer_happy_path_with_fee(self):
        self._discover()
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        before_sender = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        before_recipient = engine.get_profile("op-peer", tenant_id="tenant:acme")
        result = transfer_rail_credits(
            tenant_id="tenant:acme",
            from_operator_id="op-rewards",
            to_operator_id="op-peer",
            amount=1.0,
            trace_id="xfer-1",
            transfer_id="xfer-id-1",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "ok")
        receipt = result.get("credit_transfer_receipt") or {}
        ok, _ = verify_credit_transfer_receipt(receipt, runtime_dir=str(self.temp_root))
        self.assertTrue(ok)
        after_sender = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        after_recipient = engine.get_profile("op-peer", tenant_id="tenant:acme")
        fee = float(receipt.get("fee") or 0)
        self.assertAlmostEqual(
            after_sender["rail_credits"],
            before_sender["rail_credits"] - 1.0 - fee,
        )
        self.assertAlmostEqual(after_recipient["rail_credits"], before_recipient["rail_credits"] + 1.0)
        ledger = RewardLedger(runtime_dir=str(self.temp_root), tenant_id="tenant:acme")
        events = ledger.list_transfer_events(operator_id="op-rewards", limit=10)
        self.assertGreaterEqual(len(events), 1)

    def test_transfer_reject_self_and_low_reputation(self):
        self._discover()
        self.assertEqual(
            transfer_rail_credits(
                tenant_id="tenant:acme",
                from_operator_id="op-rewards",
                to_operator_id="op-rewards",
                amount=1,
                trace_id="xfer-self",
                runtime_dir=str(self.temp_root),
            ).get("reason"),
            "self_transfer",
        )
        self.assertEqual(
            transfer_rail_credits(
                tenant_id="tenant:acme",
                from_operator_id="op-new",
                to_operator_id="op-rewards",
                amount=1,
                trace_id="xfer-low",
                runtime_dir=str(self.temp_root),
            ).get("reason"),
            "reputation_too_low",
        )

    def test_transfer_idempotent_and_cooldown(self):
        self._discover()
        first = transfer_rail_credits(
            tenant_id="tenant:acme",
            from_operator_id="op-rewards",
            to_operator_id="op-peer",
            amount=0.5,
            trace_id="xfer-cd-1",
            transfer_id="xfer-cd-fixed",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(first.get("status"), "ok")
        second = transfer_rail_credits(
            tenant_id="tenant:acme",
            from_operator_id="op-rewards",
            to_operator_id="op-peer",
            amount=0.5,
            trace_id="xfer-cd-2",
            transfer_id="xfer-cd-fixed",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(second.get("status"), "idempotent")
        third = transfer_rail_credits(
            tenant_id="tenant:acme",
            from_operator_id="op-rewards",
            to_operator_id="op-peer",
            amount=0.5,
            trace_id="xfer-cd-3",
            transfer_id="xfer-cd-3",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(third.get("reason"), "cooldown_active")

    def test_transfer_shadow_no_balance_change(self):
        self._discover()
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "1"
        engine = OperatorRewardEngine(runtime_dir=str(self.temp_root))
        before = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        result = transfer_rail_credits(
            tenant_id="tenant:acme",
            from_operator_id="op-rewards",
            to_operator_id="op-peer",
            amount=1,
            trace_id="xfer-shadow",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "shadow")
        after = engine.get_profile("op-rewards", tenant_id="tenant:acme")
        self.assertEqual(after.get("rail_credits"), before.get("rail_credits"))

    def test_exchange_atomic(self):
        self._discover()
        discovery2 = SubsystemDiscoveryService(runtime_dir=str(self.temp_root))
        peer_spec = _valid_spec()
        peer_spec["io_shape"] = {"inputs": ["text", "image"], "outputs": ["text"]}
        discovery2.discover(
            {
                "tenant_id": "tenant:acme",
                "operator_id": "op-peer",
                "aais_instance_id": "aais-test-2",
                "spec": peer_spec,
            }
        )
        result = exchange_rail_credits(
            tenant_id="tenant:acme",
            operator_a="op-rewards",
            operator_b="op-peer",
            amount_a=0.5,
            amount_b=0.25,
            trace_id="exch-1",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(len(result.get("legs") or []), 2)

    def test_transfer_api_smoke(self):
        self._discover()
        try:
            import importlib

            importlib.import_module("src.api")
        except ModuleNotFoundError:
            self.skipTest("src.api not present")
        prior_boot = os.environ.get("AAIS_GENOME_BOOT")
        os.environ["AAIS_GENOME_BOOT"] = "warn"
        try:
            from src.api import app
        finally:
            if prior_boot is None:
                os.environ.pop("AAIS_GENOME_BOOT", None)
            else:
                os.environ["AAIS_GENOME_BOOT"] = prior_boot
        client = app.test_client()
        resp = client.post(
            "/api/ugr/reward/transfer",
            json={
                "tenant_id": "tenant:acme",
                "from_operator_id": "op-rewards",
                "to_operator_id": "op-peer",
                "amount": 0.5,
                "trace_id": "api-xfer-1",
                "transfer_id": "api-xfer-id-1",
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertIn(body.get("status"), {"ok", "idempotent", "rejected"})

    def test_reward_issue_api_smoke(self):
        first = self._discover()
        subsystem_id = str((first.get("subsystem_discovery_receipt") or {}).get("subsystem_id") or "")
        prior_boot = os.environ.get("AAIS_GENOME_BOOT")
        os.environ["AAIS_GENOME_BOOT"] = "warn"
        try:
            from src.api import app
        finally:
            if prior_boot is None:
                os.environ.pop("AAIS_GENOME_BOOT", None)
            else:
                os.environ["AAIS_GENOME_BOOT"] = prior_boot

        client = app.test_client()
        resp = client.post(
            "/api/ugr/reward/issue",
            json={
                "tenant_id": "tenant:acme",
                "operator_id": "op-rewards",
                "subsystem_id": subsystem_id,
                "event_type": EVENT_SUBSYSTEM_DISCOVERED,
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertIn(body.get("status"), {"issued", "idempotent"})

        profile_resp = client.get(
            f"/api/ugr/reward/operator/op-rewards?tenant_id=tenant:acme"
        )
        self.assertEqual(profile_resp.status_code, 200)

        ledger_resp = client.get(
            f"/api/ugr/reward/subsystem/{subsystem_id}?tenant_id=tenant:acme"
        )
        self.assertEqual(ledger_resp.status_code, 200)
        ledger_body = json.loads(ledger_resp.data)
        self.assertGreaterEqual(ledger_body.get("count", 0), 1)


if __name__ == "__main__":
    unittest.main()
