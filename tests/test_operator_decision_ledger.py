"""Operator Decision Ledger unit tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.operator_decision_ledger import (
    OperatorDecisionLedgerStore,
    append_pipeline_turn_event,
    build_decision_diff,
    evaluate_checkpoint_policy,
)


class OperatorDecisionLedgerTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        os.environ["AAIS_OPERATOR_LEDGER_PERSIST"] = "1"
        self.store = OperatorDecisionLedgerStore(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("AAIS_OPERATOR_LEDGER_PERSIST", None)
        self._tmpdir.cleanup()

    def test_append_and_verify(self):
        row = self.store.append("s1", {"decision_kind": "pipeline_turn", "decision": "allow", "reversibility": "undo_available", "summary": "turn"})
        self.assertTrue(self.store.verify_chain("s1")["valid"])
        self.assertEqual(row["decision_id"][:4], "odl_")

    def test_diff(self):
        a = self.store.append("s2", {"decision_kind": "pipeline_turn", "decision": "allow", "reversibility": "undo_available", "blast_radius": {"risk_level": "low", "affected_files": ["a.py"]}, "summary": "a"})
        b = self.store.append("s2", {"decision_kind": "otem_approval", "decision": "approve", "reversibility": "cannot_undo", "blast_radius": {"risk_level": "high", "affected_files": ["b.py"]}, "summary": "b"})
        diff = build_decision_diff("s2", a["decision_id"], b["decision_id"])
        self.assertTrue(diff["found"])
        self.assertEqual(diff["blast_radius_delta"]["risk_level_change"], "low->high")

    def test_checkpoint_blocks_critical(self):
        result = evaluate_checkpoint_policy({"drift_context": {"drift_band": "critical"}})
        self.assertEqual(result["action"], "block")

    def test_pipeline_helper(self):
        row = append_pipeline_turn_event("s3", governed_pipeline={"pipeline_id": "gdp1", "continuity_witness": {"trajectory_status": "STABLE"}}, summary="turn")
        self.assertIsNotNone(row)


if __name__ == "__main__":
    unittest.main()
