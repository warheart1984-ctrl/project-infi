"""Tests for RunLedger CISIV normalization."""

import tempfile
import unittest
from pathlib import Path

from src.run_ledger import RunLedger


class TestRunLedgerCisiv(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="run-ledger-cisiv-"))
        self.ledger = RunLedger(runtime_dir=self.temp_dir)

    def test_create_run_normalizes_verify_alias(self):
        run = self.ledger.create_run(
            session_id="sess_1",
            title="Verify routing",
            kind="operator",
            meta={"cisiv_stage": "verify"},
        )
        self.assertEqual(run["cisiv_stage"], "verification")

    def test_append_step_inherits_run_stage(self):
        run = self.ledger.create_run(
            session_id="sess_1",
            title="Patch apply",
            kind="patch_apply",
            meta={"cisiv_stage": "implementation"},
        )
        updated = self.ledger.append_step(
            run["id"],
            {
                "kind": "verify",
                "title": "Run tests",
                "summary": "Post-apply verification",
            },
        )
        self.assertEqual(updated["cisiv_stage"], "implementation")
        stored = self.ledger.get_run(run["id"])
        self.assertEqual(stored["steps"][-1]["cisiv_stage"], "implementation")

    def test_append_lifecycle_infers_verification_from_action(self):
        step = self.ledger.append_lifecycle(
            "sess_1",
            {
                "action_id": "run_pytest",
                "action_label": "Run pytest",
                "action_instance_id": "action_1",
                "stage": "executed",
                "execution_state": "completed",
            },
        )
        self.assertIsNotNone(step)
        runs = self.ledger.list_runs(session_id="sess_1", limit=1)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["current_action"]["cisiv_stage"], "verification")


if __name__ == "__main__":
    unittest.main()
