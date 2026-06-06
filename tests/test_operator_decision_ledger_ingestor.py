"""Operator decision temporal replay ingestor tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.operator_decision_ledger import OperatorDecisionLedgerStore
from src.temporal_replay.ingestors import OperatorDecisionIngestor, ingest_subject


class OperatorDecisionIngestorTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.store = OperatorDecisionLedgerStore(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_ingest_operator_session(self):
        self.store.append("ingest-s", {"decision_kind": "pipeline_turn", "decision": "allow", "reversibility": "undo_available", "summary": "ingest"})
        events = ingest_subject("operator_session", "ingest-s", runtime_dir=Path(self._tmpdir.name))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "operator_decision")


if __name__ == "__main__":
    unittest.main()
