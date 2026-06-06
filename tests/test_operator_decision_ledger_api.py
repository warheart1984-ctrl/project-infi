"""Operator Decision Ledger API tests."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import src.api as api


class OperatorDecisionLedgerApiTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.client = api.app.test_client()
        from src.operator_decision_ledger import operator_decision_ledger_store

        self.store = operator_decision_ledger_store

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_ledger_routes(self):
        row = self.store.append("api-s", {"decision_kind": "pipeline_turn", "decision": "allow", "reversibility": "undo_available", "summary": "api"})
        self.assertEqual(self.client.get("/api/operator/ledger?session_id=api-s").status_code, 200)
        self.assertEqual(self.client.get("/api/operator/ledger/digest?session_id=api-s").status_code, 200)
        self.assertEqual(self.client.get(f"/api/operator/ledger/query?session_id=api-s").status_code, 200)
        diff = self.client.get(f"/api/operator/ledger/diff?session_id=api-s&from_id={row['decision_id']}&to_id={row['decision_id']}")
        self.assertEqual(diff.status_code, 200)


if __name__ == "__main__":
    unittest.main()
