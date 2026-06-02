"""Governed-stage invariant tests for cisiv_operator_lineage_console."""

from __future__ import annotations

import unittest

from tests.test_ul_lineage import TestUlLineage


class TestCisivOperatorLineageConsole(unittest.TestCase):
    def test_governed_lineage_invariants(self) -> None:
        case = TestUlLineage()
        case.setUp()
        try:
            case.test_emit_all_node_types_multi_hop()
        finally:
            case.tearDown()


if __name__ == "__main__":
    unittest.main()
