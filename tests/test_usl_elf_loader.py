from __future__ import annotations

import unittest
from pathlib import Path

from src.usl.gate import USLGate
from src.usl.loaders.elf import guest_from_elf, load_elf, syscall_write
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class ElfLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()

    def test_load_minimal_elf_produces_ubo(self) -> None:
        ubo, address_space = load_elf(self.elf_path)
        self.assertEqual(ubo.os_family, "linux")
        self.assertEqual(ubo.architecture, "x86_64")
        self.assertTrue(ubo.binary_id.startswith("sha256:"))
        self.assertGreater(ubo.entry_point, 0)
        self.assertGreater(len(ubo.segments), 0)
        self.assertGreater(len(address_space.pages), 0)

    def test_syscall_write_binder(self) -> None:
        guest = guest_from_elf(self.elf_path, process_id="elf-guest-1")
        gate = USLGate(sign=False)
        transition, _ = syscall_write(
            guest,
            "/tmp/usl-elf-test.txt",
            b"elf-data",
            gate,
        )
        self.assertEqual(transition.capability.capability_id, "fs.write")
        self.assertEqual(transition.context.os_family, "linux")
        self.assertEqual(transition.actor.binary_id, guest.ubo.binary_id)


if __name__ == "__main__":
    unittest.main()
