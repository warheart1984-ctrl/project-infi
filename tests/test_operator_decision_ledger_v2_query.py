"""ODL v2 index query tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.operator_decision_ledger import OperatorDecisionLedgerStore
from src.operator_decision_ledger_index import OperatorDecisionLedgerIndex


class ODLV2QueryTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.store = OperatorDecisionLedgerStore(runtime_dir=Path(self._tmpdir.name))
        self.index = OperatorDecisionLedgerIndex(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_query_and_chain(self):
        first = self.store.append("q", {"decision_kind": "pipeline_turn", "decision": "allow", "reversibility": "undo_available", "summary": "a"})
        second = self.store.append("q", {"decision_kind": "otem_approval", "decision": "pending", "reversibility": "undo_available", "causal_parents": [first["decision_id"]], "summary": "b"})
        q = self.index.query_index("q", pending_only=True)
        self.assertEqual(q["count"], 1)
        chain = self.index.shortest_causal_chain("q", first["decision_id"], second["decision_id"])
        self.assertTrue(chain["found"])


if __name__ == "__main__":
    unittest.main()
