"""Tests for Trust Root measurement chain."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.ucr.boot_manifest import build_boot_manifest, parse_boot_manifest, write_boot_manifest
from src.ucr.corridor import build_nova_dev_corridor, build_prod_ops_corridor
from src.ucr.corridor_loader import reset_corridor_loader_for_tests, write_corridor_fixture
from src.ucr.corridor_serialize import TrustedCorridorSet
from src.ucr.hash_utils import digest_bytes
from src.ucr.kernel_boot import run_early_boot
from src.ucr.law_spine_pack import canonical_pack, compute_h_law_spine
from src.ucr.trust_root import (
    TRUST_ROOT_DOMAIN,
    TrustRoot,
    build_trust_root,
    compute_h_trust_root,
    get_trust_root,
    reset_trust_root_for_tests,
    to_ucr_context,
)
from src.ucr.ucr_governed import require_governed_mode


class TrustRootTests(unittest.TestCase):
    BOOT_TS = "2026-06-18T10:00:00Z"

    def setUp(self) -> None:
        reset_trust_root_for_tests()
        reset_corridor_loader_for_tests()

    def tearDown(self) -> None:
        reset_trust_root_for_tests()
        reset_corridor_loader_for_tests()

    def test_individual_measurements(self) -> None:
        kernel_digest = digest_bytes(b"aaes-kernel-image-stub-v0.1")
        self.assertEqual(len(kernel_digest), 32)
        modules = {"LAW_CONS_v1": b"cons", "LAW_SPINE_UCR_v0.1": b"ucr"}
        law_spine = canonical_pack(modules)
        self.assertTrue(law_spine.startswith(b"LAW_CONS_v1"))
        self.assertTrue(compute_h_law_spine(modules).startswith("sha3-256:"))

    def test_h_boot_manifest_excludes_self_line(self) -> None:
        manifest = build_boot_manifest(
            h_kernel_image="sha3-256:" + "a" * 64,
            h_law_spine="sha3-256:" + "b" * 64,
            h_corridors="sha3-256:" + "c" * 64,
            boot_timestamp=self.BOOT_TS,
        )
        self.assertNotIn(b"H_BOOT_MANIFEST=", manifest.raw_without_self)
        self.assertTrue(manifest.h_boot_manifest.startswith("sha3-256:"))

    def test_h_trust_root_order_sensitive(self) -> None:
        a = "sha3-256:" + "1" * 64
        b = "sha3-256:" + "2" * 64
        c = "sha3-256:" + "3" * 64
        d = "sha3-256:" + "4" * 64
        root_ab = compute_h_trust_root(h_kernel_image=a, h_law_spine=b, h_corridors=c, h_boot_manifest=d)
        root_ba = compute_h_trust_root(h_kernel_image=b, h_law_spine=a, h_corridors=c, h_boot_manifest=d)
        self.assertNotEqual(root_ab, root_ba)

    def test_domain_separator_required(self) -> None:
        manifest = build_boot_manifest(
            h_kernel_image="sha3-256:" + "1" * 64,
            h_law_spine="sha3-256:" + "2" * 64,
            h_corridors="sha3-256:" + "3" * 64,
            boot_timestamp=self.BOOT_TS,
        )
        trust_root = build_trust_root(manifest)
        payload = TRUST_ROOT_DOMAIN + b"\x01" * 128
        alt = "sha3-256:" + digest_bytes(payload).hex()
        self.assertNotEqual(trust_root.h_trust_root, alt)

    def test_ucr_context_exposure(self) -> None:
        manifest = build_boot_manifest(
            h_kernel_image="sha3-256:" + "1" * 64,
            h_law_spine="sha3-256:" + "2" * 64,
            h_corridors="sha3-256:" + "3" * 64,
            boot_timestamp=self.BOOT_TS,
        )
        trust_root = build_trust_root(manifest)
        context = to_ucr_context(trust_root)
        self.assertEqual(context.h_trust_root, trust_root.h_trust_root)
        self.assertEqual(context.h_corridors, trust_root.h_corridors)

    def test_governed_mode_refuses_mismatch(self) -> None:
        manifest = build_boot_manifest(
            h_kernel_image="sha3-256:" + "1" * 64,
            h_law_spine="sha3-256:" + "2" * 64,
            h_corridors="sha3-256:" + "3" * 64,
            boot_timestamp=self.BOOT_TS,
        )
        trust_root = build_trust_root(manifest)
        context = to_ucr_context(trust_root)
        refusal = require_governed_mode(
            context,
            trust_root,
            ucr_law_view="sha3-256:" + "9" * 64,
            ucr_corridor_view=trust_root.h_corridors,
        )
        self.assertIsNotNone(refusal)
        self.assertEqual(refusal.reason_code, 1006)

    def test_end_to_end_boot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "corridors"
            registry.mkdir(parents=True)
            write_corridor_fixture(registry, build_nova_dev_corridor())
            write_corridor_fixture(registry, build_prod_ops_corridor())
            kernel_image = Path(tmp) / "kernel.bin"
            kernel_image.write_bytes(b"aaes-kernel-image-stub-v0.1")
            result = run_early_boot(
                registry,
                kernel_image_path=kernel_image,
                boot_timestamp=self.BOOT_TS,
            )
            self.assertEqual(result.boot_result.value, "OK")
            assert result.trust_root is not None
            sealed = get_trust_root()
            self.assertEqual(sealed.h_trust_root, result.trust_root.h_trust_root)

            manifest_path = Path(tmp) / "boot.manifest"
            assert result.manifest is not None
            write_boot_manifest(manifest_path, result.manifest)
            parsed = parse_boot_manifest(manifest_path)
            self.assertEqual(parsed["H_CORRIDORS"], result.manifest.h_corridors)
            self.assertTrue(parsed["H_BOOT_MANIFEST"].startswith("sha3-256:"))


if __name__ == "__main__":
    unittest.main()
