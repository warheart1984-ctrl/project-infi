from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class UniversalSubstrateTests(unittest.TestCase):
    def test_installer_substrate_ids_registered(self) -> None:
        registry = REPO_ROOT / "cog-os" / "forge" / "substrates" / "registry.json"
        if not registry.is_file():
            self.skipTest("cog-os substrate registry missing")
        text = registry.read_text(encoding="utf-8")
        for substrate_id in ("windows-installer", "macos-installer", "android-bootable"):
            self.assertIn(substrate_id, text)


if __name__ == "__main__":
    unittest.main()
