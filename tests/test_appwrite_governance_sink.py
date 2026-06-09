"""Tests for optional Appwrite governance sink."""

from __future__ import annotations

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.appwrite_governance_sink import (
    appwrite_sink_enabled,
    contract_rows_from_paths,
    maybe_mirror_ledger_event,
    upsert_governance_contracts,
)


class AppwriteGovernanceSinkTests(unittest.TestCase):
    def tearDown(self):
        for key in (
            "AAIS_APPWRITE_SINK",
            "APPWRITE_ENDPOINT",
            "APPWRITE_PROJECT_ID",
            "APPWRITE_API_KEY",
            "APPWRITE_DATABASE_ID",
        ):
            os.environ.pop(key, None)

    def test_disabled_by_default(self):
        self.assertFalse(appwrite_sink_enabled())

    def test_enabled_when_configured(self):
        os.environ["AAIS_APPWRITE_SINK"] = "1"
        os.environ["APPWRITE_ENDPOINT"] = "https://cloud.appwrite.io/v1"
        os.environ["APPWRITE_PROJECT_ID"] = "proj"
        os.environ["APPWRITE_API_KEY"] = "key"
        os.environ["APPWRITE_DATABASE_ID"] = "governance"
        self.assertTrue(appwrite_sink_enabled())

    def test_contract_rows_from_paths(self):
        rows = contract_rows_from_paths(
            ["docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md"],
            root=os.path.join(os.path.dirname(__file__), ".."),
        )
        self.assertEqual(len(rows), 1)
        self.assertIn("AAIS ADAPTIVE GOVERNANCE", rows[0]["title"])

    def test_upsert_skipped_when_disabled(self):
        result = upsert_governance_contracts([{"path": "x", "content": "y"}])
        self.assertFalse(result["enabled"])
        self.assertEqual(result["upserted"], 0)

    @patch("src.appwrite_governance_sink._client")
    def test_upsert_creates_new_row(self, client_factory):
        fake_id = SimpleNamespace(unique=lambda: "row_new")
        fake_query = SimpleNamespace(equal=lambda *a, **k: "eq", limit=lambda n: "lim")
        sys.modules["appwrite.id"] = SimpleNamespace(ID=fake_id)
        sys.modules["appwrite.query"] = SimpleNamespace(Query=fake_query)

        os.environ["AAIS_APPWRITE_SINK"] = "1"
        os.environ["APPWRITE_ENDPOINT"] = "https://cloud.appwrite.io/v1"
        os.environ["APPWRITE_PROJECT_ID"] = "proj"
        os.environ["APPWRITE_API_KEY"] = "key"
        os.environ["APPWRITE_DATABASE_ID"] = "governance"

        tables_db = MagicMock()
        tables_db.list_rows.return_value = {"rows": []}
        client_factory.return_value = (MagicMock(), tables_db)

        result = upsert_governance_contracts(
            [{"path": "docs/contracts/test.md", "title": "Test", "content": "body"}]
        )
        self.assertTrue(result["enabled"])
        self.assertEqual(result["upserted"], 1)
        tables_db.create_row.assert_called_once()

    def test_maybe_mirror_swallows_errors(self):
        with patch(
            "src.appwrite_governance_sink.mirror_ledger_event",
            side_effect=RuntimeError("network"),
        ):
            maybe_mirror_ledger_event("s1", {"decision_id": "odl_test"})


if __name__ == "__main__":
    unittest.main()
