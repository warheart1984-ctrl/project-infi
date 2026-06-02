"""Governed-stage invariant tests for forensic_triangulation."""

from __future__ import annotations

import unittest

from tests.test_triangulation import TestTriangulation


class TestForensicTriangulation(unittest.TestCase):
    def test_governed_triangulation_invariants(self) -> None:
        case = TestTriangulation()
        case.setUp()
        try:
            case.test_fixture_correlates_with_proven_edge()
        finally:
            case.tearDown()


if __name__ == "__main__":
    unittest.main()
