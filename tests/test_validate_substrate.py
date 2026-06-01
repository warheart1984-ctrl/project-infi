from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLASSIFY = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "substrate_classify.py"


def _load_classify():
    lib_dir = str(CLASSIFY.parent)
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)
    spec = importlib.util.spec_from_file_location("substrate_classify", CLASSIFY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateSubstrateRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sc = _load_classify()

    def test_registry_v2_loads(self) -> None:
        registry_path = REPO_ROOT / "wolf-cog-os" / "forge" / "substrates" / "registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(registry["registry_version"], "substrate-registry.v2")
        self.assertIn("ubuntu-live", registry["substrates"])
        self.assertIn("arch-live", registry["substrates"])

    def test_resolve_extends_generic_profile(self) -> None:
        registry = {
            "substrates": {
                "generic-live-squashfs": {
                    "detect": {"path_globs": ["live/*.squashfs"], "path_any": ["live/vmlinuz"]},
                    "min_bytes": 100,
                },
                "cogos-replay": {
                    "extends": "generic-live-squashfs",
                    "priority": 90,
                    "min_bytes": 1000,
                    "detect": {"path_globs": ["live/filesystem.squashfs"], "path_any": ["boot/grub/grub.cfg"]},
                },
            }
        }
        effective_id, spec = self.sc.resolve_spec(registry, "cogos-replay")
        self.assertEqual(effective_id, "cogos-replay")
        self.assertGreaterEqual(spec.get("min_bytes", 0), 1000)
        globs = spec.get("detect", {}).get("path_globs", [])
        self.assertIn("live/*.squashfs", globs)
        self.assertIn("live/filesystem.squashfs", globs)

    def test_classification_prefers_cogos_over_generic(self) -> None:
        registry = {
            "default_substrate_id": "generic-live-squashfs",
            "substrates": {
                "generic-live-squashfs": {
                    "priority": 10,
                    "detect": {"path_globs": ["live/*.squashfs"], "path_any": ["live/vmlinuz"]},
                },
                "cogos-replay": {
                    "extends": "generic-live-squashfs",
                    "priority": 90,
                    "detect": {
                        "path_globs": ["live/filesystem.squashfs"],
                        "path_any": ["boot/grub/grub.cfg"],
                        "path_markers": ["live/filesystem.packages"],
                    },
                },
            },
        }
        paths = {
            "live/filesystem.squashfs",
            "live/vmlinuz",
            "boot/grub/grub.cfg",
            "live/filesystem.packages",
        }
        result = self.sc.classify_with_confidence(registry, paths)
        self.assertEqual(result["substrate_id"], "cogos-replay")
        self.assertGreater(result["confidence"], 0)

    def test_multi_distro_classes_registered(self) -> None:
        registry_path = REPO_ROOT / "wolf-cog-os" / "forge" / "substrates" / "registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for substrate_id in ("ubuntu-live", "arch-live", "fedora-live", "alpine-live", "opensuse-live"):
            row = registry["substrates"][substrate_id]
            self.assertTrue(row.get("replay_adapter"))
            self.assertEqual(row.get("contract_version"), "forge-substrate.v2")


if __name__ == "__main__":
    unittest.main()
