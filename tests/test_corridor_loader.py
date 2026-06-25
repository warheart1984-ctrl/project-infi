"""Tests for Corridor Loader (CRG_LOADER)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from src.ucr.binary_law_key import CANONICAL_U128
from src.ucr.corridor import NOVA_DEV_CORRIDOR_ID, build_nova_dev_corridor
from src.ucr.corridor_loader import (
    CorridorLoader,
    CorridorLoaderError,
    ERR_CORRIDOR_MALFORMED,
    ERR_NO_CORRIDORS,
    get_trusted_corridors,
    is_sealed,
    reset_corridor_loader_for_tests,
    write_corridor_fixture,
)
from src.ucr.corridor_registry import get_corridor, reset_registry
from src.ucr.trust_root import reset_trust_root_for_tests


class CorridorLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_corridor_loader_for_tests()
        reset_registry()
        reset_trust_root_for_tests()

    def tearDown(self) -> None:
        reset_corridor_loader_for_tests()
        reset_registry()
        reset_trust_root_for_tests()

    def test_discover_nova_dev_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp)
            write_corridor_fixture(registry, build_nova_dev_corridor())
            loader = CorridorLoader()
            trusted = loader.load_and_seal(registry, law_spine_key=CANONICAL_U128, boot_timestamp="2026-06-18T10:00:00Z")
            self.assertTrue(is_sealed())
            self.assertEqual(len(trusted.corridors), 1)
            self.assertEqual(trusted.corridors[0].name, "Nova-Dev")

    def test_no_corridors_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loader = CorridorLoader()
            with self.assertRaises(CorridorLoaderError) as ctx:
                loader.load_and_seal(Path(tmp), law_spine_key=CANONICAL_U128)
            self.assertEqual(ctx.exception.code, ERR_NO_CORRIDORS)

    def test_malformed_manifest_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp)
            bad_dir = registry / f"corridor_{uuid4()}"
            bad_dir.mkdir(parents=True)
            (bad_dir / "manifest.json").write_text("{}", encoding="utf-8")
            loader = CorridorLoader()
            with self.assertRaises(CorridorLoaderError) as ctx:
                loader.load_and_seal(registry, law_spine_key=CANONICAL_U128)
            self.assertEqual(ctx.exception.code, ERR_CORRIDOR_MALFORMED)

    def test_sealed_registry_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp)
            write_corridor_fixture(registry, build_nova_dev_corridor())
            CorridorLoader().load_and_seal(registry, law_spine_key=CANONICAL_U128, boot_timestamp="2026-06-18T10:00:00Z")
            corridor = get_corridor(NOVA_DEV_CORRIDOR_ID)
            self.assertIsNotNone(corridor)
            self.assertEqual(get_trusted_corridors().corridor_hash.count(":"), 1)


if __name__ == "__main__":
    unittest.main()
