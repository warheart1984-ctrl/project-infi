from __future__ import annotations

import unittest
from pathlib import Path

from src.usl.lift import lift_machine_code
from src.usl.loaders.pe import load_pe
from tests.fixtures.usl.build_fixtures import ensure_fixtures, ensure_windows_syscall_pe


class ULLiftPETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.pe_path = ensure_fixtures()
        cls.syscall_pe_path = ensure_windows_syscall_pe()

    def test_lift_minimal_pe_meta_and_control(self) -> None:
        ubo, _ = load_pe(self.pe_path)
        model = lift_machine_code(ubo, source_path=str(self.pe_path))

        self.assertEqual(model.meta.program_id, ubo.binary_id)
        self.assertEqual(model.meta.format, "pe")
        self.assertEqual(model.meta.os_family, "windows")
        self.assertEqual(model.meta.architecture, "x86_64")
        self.assertGreater(len(model.control.blocks), 0)

    def test_lift_windows_syscall_pe_effects(self) -> None:
        ubo, _ = load_pe(self.syscall_pe_path)
        model = lift_machine_code(ubo, source_path=str(self.syscall_pe_path))

        self.assertEqual(model.meta.os_family, "windows")
        self.assertGreaterEqual(len(model.effects.syscalls), 1)
        sc = model.effects.syscalls[0]
        self.assertEqual(sc.syscall_number, 1)
        self.assertEqual(sc.syscall_name, "write")
        self.assertEqual(sc.bucket, "fs")
        self.assertEqual(sc.confidence, "proven")
        rule_ids = {r.invariant_id for r in model.invariants.rules}
        self.assertNotIn("inv-no-syscall", rule_ids)

    def test_lift_pe_from_bytes_matches_file_loader(self) -> None:
        raw = Path(self.pe_path).read_bytes()
        from src.usl.loaders.pe import load_pe_bytes

        ubo_file, _ = load_pe(self.pe_path)
        ubo_bytes, _ = load_pe_bytes(raw, source_path=str(self.pe_path))
        model = lift_machine_code(ubo_bytes)
        self.assertEqual(model.meta.program_id, ubo_file.binary_id)


if __name__ == "__main__":
    unittest.main()
