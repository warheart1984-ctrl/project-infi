from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ValidateSubstrateTests(unittest.TestCase):
    def test_cog_os_substrate_registry_exists(self) -> None:
        registry = REPO_ROOT / "cog-os" / "forge" / "substrates" / "registry.json"
        self.assertTrue(registry.is_file(), msg=f"missing {registry}")
        payload = json.loads(registry.read_text(encoding="utf-8"))
        self.assertIn("substrates", payload)


if __name__ == "__main__":
    unittest.main()
