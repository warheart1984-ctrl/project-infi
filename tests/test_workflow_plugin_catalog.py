"""Workflow plugin catalog tests."""

from __future__ import annotations

import unittest

from src.workflow_plugin_catalog import list_pending_plug_steps, list_workflow_bundles


class WorkflowPluginCatalogTests(unittest.TestCase):
    def test_list_bundles(self):
        bundles = list_workflow_bundles()
        self.assertGreaterEqual(len(bundles), 20)
        ids = {b["workflow_id"] for b in bundles}
        self.assertIn("research_brief", ids)

    def test_list_pending_plug_steps(self):
        pending = list_pending_plug_steps()
        self.assertIsInstance(pending, list)
        for row in pending:
            self.assertEqual(row.get("status"), "pending_plug")


if __name__ == "__main__":
    unittest.main()
