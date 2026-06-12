from __future__ import annotations

import unittest
from pathlib import Path

from src.usl.lift import lift_machine_code
from src.usl.loaders.elf import load_elf
from tests.fixtures.usl.build_fixtures import ensure_aarch64_elf


class ULLiftAarch64Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aarch64_elf_path = ensure_aarch64_elf()

    def test_lift_aarch64_elf_meta_and_architecture(self) -> None:
        ubo, _ = load_elf(self.aarch64_elf_path)
        model = lift_machine_code(ubo, source_path=str(self.aarch64_elf_path))

        self.assertEqual(model.meta.architecture, "aarch64")
        self.assertEqual(model.meta.os_family, "linux")
        self.assertEqual(model.meta.format, "elf")
        self.assertGreater(len(model.control.blocks), 0)

    def test_lift_aarch64_syscall_effects(self) -> None:
        ubo, _ = load_elf(self.aarch64_elf_path)
        model = lift_machine_code(ubo, source_path=str(self.aarch64_elf_path))

        self.assertGreaterEqual(len(model.effects.syscalls), 1)
        sc = model.effects.syscalls[0]
        self.assertEqual(sc.syscall_number, 1)
        self.assertEqual(sc.syscall_name, "write")
        self.assertEqual(sc.bucket, "fs")
        self.assertEqual(sc.confidence, "proven")


if __name__ == "__main__":
    unittest.main()
