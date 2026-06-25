"""Tests for canonical H_CORRIDORS measurement."""

from __future__ import annotations

import unittest

from src.ucr.corridor import build_nova_dev_corridor, build_prod_ops_corridor
from src.ucr.corridor_serialize import TrustedCorridorSet, compute_h_corridors, serialize_trusted_corridor_set


class HCorridorsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timestamp = "2026-06-18T10:00:00Z"
        self.corridors = [build_nova_dev_corridor(), build_prod_ops_corridor()]

    def test_canonical_json_stable(self) -> None:
        trusted_a = TrustedCorridorSet.from_corridors(
            self.corridors,
            registry_version=1,
            boot_timestamp=self.timestamp,
        )
        trusted_b = TrustedCorridorSet.from_corridors(
            list(reversed(self.corridors)),
            registry_version=1,
            boot_timestamp=self.timestamp,
        )
        self.assertEqual(
            serialize_trusted_corridor_set(trusted_a),
            serialize_trusted_corridor_set(trusted_b),
        )
        self.assertEqual(trusted_a.corridor_hash, trusted_b.corridor_hash)

    def test_format_line(self) -> None:
        trusted = TrustedCorridorSet.from_corridors(
            self.corridors,
            registry_version=1,
            boot_timestamp=self.timestamp,
        )
        self.assertTrue(trusted.corridor_hash.startswith("sha3-256:"))
        self.assertEqual(len(trusted.corridor_hash.split(":", 1)[1]), 64)

    def test_snapshot_digest(self) -> None:
        trusted = TrustedCorridorSet.from_corridors(
            self.corridors,
            registry_version=1,
            boot_timestamp=self.timestamp,
        )
        self.assertEqual(trusted.corridor_hash, compute_h_corridors(trusted))
        self.assertEqual(
            trusted.corridor_hash,
            "sha3-256:732b66373c6d66281ff95fa69fe3ff1a0d8c8fa70cc2ae13245e6d1890372cda",
        )


if __name__ == "__main__":
    unittest.main()
