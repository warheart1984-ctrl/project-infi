"""Library registry tests."""

from __future__ import annotations

import unittest

from src.library_registry import list_libraries


class LibraryRegistryTests(unittest.TestCase):
    def test_list_libraries(self):
        libs = list_libraries()
        self.assertGreaterEqual(len(libs), 50)


if __name__ == "__main__":
    unittest.main()
