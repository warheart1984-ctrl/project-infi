from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class RootfsBackendTests(unittest.TestCase):
    def test_debootstrap_backend_registered(self) -> None:
        registry = REPO_ROOT / "cog-os" / "forge" / "backends" / "registry.json"
        self.assertTrue(registry.is_file(), msg=f"missing {registry}")
        payload = json.loads(registry.read_text(encoding="utf-8"))
        backends = payload.get("backends", {})
        self.assertIn("debootstrap", backends)


if __name__ == "__main__":
    unittest.main()
