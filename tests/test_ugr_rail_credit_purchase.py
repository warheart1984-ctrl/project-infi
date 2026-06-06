"""Tests for ledger-only rail credit purchase."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.rewards.purchase_receipt import build_purchase_receipt, verify_purchase_receipt
from src.ugr.rewards.rail_credit_purchase import purchase_rail_credits
from src.ugr.rewards.rail_credit_spend import spend_rail_credits
from src.ugr.rewards.reward_ledger import RewardLedger


class TestRailCreditPurchase(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-purchase-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-purchase-key"
        os.environ["UGR_OPERATOR_REWARDS_ENABLED"] = "1"
        os.environ["UGR_RAIL_CREDIT_PURCHASE_ENABLED"] = "1"
        os.environ["UGR_RAIL_CREDIT_SPEND_ENABLED"] = "1"
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "0"

    def tearDown(self):
        for key in (
            "AAIS_RUNTIME_DIR",
            "URG_RECEIPT_SIGNING_KEY",
            "UGR_OPERATOR_REWARDS_ENABLED",
            "UGR_RAIL_CREDIT_PURCHASE_ENABLED",
            "UGR_RAIL_CREDIT_SPEND_ENABLED",
            "UGR_REWARDS_SHADOW_ONLY",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_purchase_mints_purchased_balance(self):
        result = purchase_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-buyer",
            amount=10,
            payment_reference="invoice-001",
            trace_id="trace-purchase-1",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(result.get("status"), "ok")
        profile = result.get("profile") or {}
        self.assertEqual(profile.get("purchased_rail_credits"), 10.0)
        self.assertEqual(profile.get("reputation_score"), 0.0)

    def test_purchase_idempotent(self):
        receipt = build_purchase_receipt(
            tenant_id="tenant:acme",
            operator_id="op-buyer",
            amount=5,
            payment_reference="invoice-002",
            runtime_dir=str(self.temp_root),
        )
        first = purchase_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-buyer",
            amount=5,
            payment_reference="invoice-002",
            trace_id="trace-purchase-2",
            purchase_receipt=receipt,
            runtime_dir=str(self.temp_root),
        )
        second = purchase_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-buyer",
            amount=5,
            payment_reference="invoice-002",
            trace_id="trace-purchase-2b",
            purchase_receipt=receipt,
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(first.get("status"), "ok")
        self.assertEqual(second.get("status"), "idempotent")

    def test_purchased_spend_without_reputation(self):
        purchase_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-buyer",
            amount=3,
            payment_reference="invoice-003",
            trace_id="trace-purchase-3",
            runtime_dir=str(self.temp_root),
        )
        spend = spend_rail_credits(
            tenant_id="tenant:acme",
            operator_id="op-buyer",
            amount=1,
            trace_id="trace-spend-1",
            runtime_dir=str(self.temp_root),
        )
        self.assertEqual(spend.get("status"), "ok")
        self.assertIn("forge_boost", spend)
        profile = spend.get("profile") or {}
        self.assertEqual(profile.get("purchased_rail_credits"), 2.0)

    def test_verify_purchase_receipt(self):
        receipt = build_purchase_receipt(
            tenant_id="tenant:acme",
            operator_id="op-buyer",
            amount=1,
            payment_reference="inv",
            runtime_dir=str(self.temp_root),
        )
        ok, reason = verify_purchase_receipt(receipt, runtime_dir=str(self.temp_root))
        self.assertTrue(ok, reason)


if __name__ == "__main__":
    unittest.main()
