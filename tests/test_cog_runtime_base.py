"""Tests for cog_runtime base session and ledger."""

import unittest

from src.cog_runtime.base import CogRuntimeSession


class TestCogRuntimeBase(unittest.TestCase):
    def test_stages_must_be_ordered(self):
        session = CogRuntimeSession(
            runtime_id="test.runtime",
            user_message="hello",
            required_stages=("alpha", "beta"),
            stage_order=("alpha", "beta"),
        )
        session.start_stage("beta", {})
        session.end_stage("beta", {"ok": True})
        session.start_stage("alpha", {})
        session.end_stage("alpha", {"ok": True})

        validation = session.validate_turn()
        self.assertFalse(validation["valid"])
        self.assertTrue(any("stage_order_violation" in issue for issue in validation["issues"]))

    def test_ledger_is_append_only_via_end_stage(self):
        session = CogRuntimeSession(
            runtime_id="test.runtime",
            user_message="hello",
            required_stages=("alpha",),
            stage_order=("alpha",),
        )
        session.start_stage("alpha", {"in": 1})
        session.end_stage("alpha", {"out": 2})
        ledger = session.export_ledger()
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["stage"], "alpha")
        self.assertEqual(ledger[0]["payload"]["in"], 1)
        self.assertEqual(ledger[0]["result"]["out"], 2)

    def test_validate_turn_requires_closed_stages(self):
        session = CogRuntimeSession(
            runtime_id="test.runtime",
            user_message="hello",
            required_stages=("alpha", "beta"),
            stage_order=("alpha", "beta"),
        )
        session.start_stage("alpha", {})
        session.end_stage("alpha", {})
        validation = session.validate_turn()
        self.assertFalse(validation["valid"])
        self.assertIn("missing_required:beta", validation["issues"])


if __name__ == "__main__":
    unittest.main()
