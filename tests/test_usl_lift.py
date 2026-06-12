from __future__ import annotations

import unittest
from pathlib import Path

from src.usl.lift import lift_machine_code
from src.usl.loaders.elf import load_elf
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class ULLiftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()

    def test_lift_minimal_elf_meta_and_control(self) -> None:
        ubo, _ = load_elf(self.elf_path)
        model = lift_machine_code(ubo, source_path=str(self.elf_path))

        self.assertEqual(model.meta.program_id, ubo.binary_id)
        self.assertEqual(model.meta.provenance.artifact_hash, ubo.binary_id)
        self.assertEqual(model.meta.architecture, "x86_64")
        self.assertEqual(model.meta.os_family, "linux")
        self.assertEqual(model.meta.entry_point, ubo.entry_point)
        self.assertGreater(len(model.control.blocks), 0)
        entry_blocks = [b for b in model.control.blocks if b.start_vaddr == ubo.entry_point]
        self.assertEqual(len(entry_blocks), 1)

    def test_lift_minimal_elf_effects_invariants_capabilities(self) -> None:
        ubo, _ = load_elf(self.elf_path)
        model = lift_machine_code(ubo)

        self.assertEqual(len(model.effects.syscalls), 0)
        rule_ids = {r.invariant_id for r in model.invariants.rules}
        self.assertIn("inv-no-syscall", rule_ids)
        self.assertEqual(model.capabilities.ceiling_id, "containment")
        self.assertEqual(len(model.capabilities.resources), 0)

    def test_lift_from_bytes_matches_file_loader(self) -> None:
        raw = Path(self.elf_path).read_bytes()
        from src.usl.loaders.elf import load_elf_bytes

        ubo_file, _ = load_elf(self.elf_path)
        ubo_bytes, _ = load_elf_bytes(raw, source_path=str(self.elf_path))
        model = lift_machine_code(ubo_bytes)
        self.assertEqual(model.meta.program_id, ubo_file.binary_id)


if __name__ == "__main__":
    unittest.main()
