"""Plug discovery tests."""

from __future__ import annotations

import unittest

from src.plug_discovery import discover_plugs


class PlugDiscoveryTests(unittest.TestCase):
    def test_discover_plugs_non_empty(self):
        plugs = discover_plugs()
        self.assertGreater(len(plugs), 10)
        self.assertEqual(plugs[0]["plug_adapter_version"], "plug_adapter.v1")


if __name__ == "__main__":
    unittest.main()
