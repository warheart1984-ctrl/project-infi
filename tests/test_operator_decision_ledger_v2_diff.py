"""ODL v2 diff tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.operator_decision_ledger import OperatorDecisionLedgerStore, build_decision_diff


class ODLV2DiffTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.store = OperatorDecisionLedgerStore(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_diff_kind_change(self):
        a = self.store.append("d", {"decision_kind": "pipeline_turn", "decision": "allow", "reversibility": "undo_available", "summary": "a"})
        b = self.store.append("d", {"decision_kind": "otem_approval", "decision": "approve", "reversibility": "cannot_undo", "summary": "b"})
        diff = build_decision_diff("d", a["decision_id"], b["decision_id"])
        self.assertEqual(diff["decision_kind_change"], "pipeline_turn->otem_approval")


if __name__ == "__main__":
    unittest.main()
