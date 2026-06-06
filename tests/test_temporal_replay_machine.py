"""Invariant tests for temporal_replay_machine genome promotion."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.operator_decision_ledger import OperatorDecisionLedgerStore
from src.temporal_replay.service import build_timeline, verify_timeline


class TemporalReplayMachineInvariantTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.store = OperatorDecisionLedgerStore(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_timeline_ingests_operator_decision_events(self):
        scope = "replay-scope"
        self.store.append(
            scope,
            {
                "decision_kind": "pipeline_turn",
                "decision": "allow",
                "reversibility": "undo_available",
                "summary": "replay test",
            },
        )
        timeline = build_timeline("operator_session", scope, runtime_dir=Path(self._tmpdir.name))
        self.assertGreaterEqual(timeline["event_count"], 1)
        verification = verify_timeline(timeline)
        self.assertTrue(verification["valid"])


if __name__ == "__main__":
    unittest.main()
