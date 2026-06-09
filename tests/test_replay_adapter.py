from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ReplayAdapterTests(unittest.TestCase):
    def test_cogos_replay_substrate_registered(self) -> None:
        registry = REPO_ROOT / "cog-os" / "forge" / "substrates" / "registry.json"
        if not registry.is_file():
            self.skipTest("cog-os substrate registry missing")
        text = registry.read_text(encoding="utf-8")
        self.assertIn("cogos-replay", text)


if __name__ == "__main__":
    unittest.main()
