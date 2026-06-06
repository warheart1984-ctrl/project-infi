"""MCP bridge tests."""

from __future__ import annotations

import unittest

from src.mcp_bridge import invoke_mcp_plug, list_mcp_plugs


class McpBridgeTests(unittest.TestCase):
    def test_list_and_invoke(self):
        plugs = list_mcp_plugs()
        self.assertGreater(len(plugs), 0)
        result = invoke_mcp_plug(plugs[0]["plug_id"], dry_run=True)
        self.assertEqual(result["outcome"], "dry_run")


if __name__ == "__main__":
    unittest.main()
