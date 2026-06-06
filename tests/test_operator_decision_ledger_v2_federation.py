"""ODL v2 federation graph tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.operator_decision_ledger import (
    OperatorDecisionLedgerStore,
    append_federated_peer_decision_event,
    build_federation_graph,
)


class ODLV2FederationTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.store = OperatorDecisionLedgerStore(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_federation_graph(self):
        grant = "grant-001"
        home = self.store.append(
            "fed",
            {
                "decision_kind": "urg_receipt",
                "decision": "completed",
                "reversibility": "cannot_undo",
                "federation": {"grant_id": grant, "federation_digest": "abc", "counterparty_receipt_ref": {"tenant_id": "tenant:peer", "grant_id": grant}},
                "summary": "home",
            },
        )
        append_federated_peer_decision_event("fed", grant_id=grant, federation_digest="abc", counterparty_receipt_ref={"tenant_id": "tenant:peer", "grant_id": grant}, parent_decision_id=home["decision_id"])
        graph = build_federation_graph(grant, home_scope="fed")
        self.assertEqual(len(graph["home_nodes"]), 1)


if __name__ == "__main__":
    unittest.main()
