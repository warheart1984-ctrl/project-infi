from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.cloud_forge.types import LawEnvelope
from src.usl.forge.compiler import ForgeCompiler
from src.usl.forge.dynamic_emitter import DynamicForgeBundle, emit_dynamic
from src.usl.forge.static_emitter import StaticForgeImageRef, emit_static
from src.usl.lift import lift_machine_code
from src.usl.loaders.elf import load_elf
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class USLForgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()
        cls.law = LawEnvelope(law_id="test-law", law_version="1")

    def setUp(self) -> None:
        ubo, _ = load_elf(self.elf_path)
        self.model = lift_machine_code(ubo, source_path=str(self.elf_path))

    def test_emit_dynamic_bundle_shape(self) -> None:
        bundle = emit_dynamic(self.model, law=self.law, domain=None)
        self.assertIsInstance(bundle, DynamicForgeBundle)
        self.assertEqual(bundle.program_id, self.model.meta.program_id)
        self.assertIn("law_id", bundle.law_bundle)
        self.assertEqual(bundle.capability_bindings["ceiling_id"], "containment")
        self.assertEqual(bundle.broker_profile["program_id"], self.model.meta.program_id)
        self.assertIn("admission_invariants", bundle.gate_policy)
        self.assertIn("inv-no-syscall", bundle.gate_policy["all_invariants"])
        self.assertIsInstance(bundle.governance_decode_bundle, dict)
        self.assertIn("check_graph", bundle.governance_decode_bundle)

    def test_forge_compiler_dynamic_mode(self) -> None:
        out = ForgeCompiler.emit(self.model, mode="dynamic", law=self.law)
        self.assertIsInstance(out, DynamicForgeBundle)

    def test_emit_static_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ref = emit_static(self.model, law=self.law, rootfs_dir=root)
            self.assertIsInstance(ref, StaticForgeImageRef)
            self.assertEqual(ref.program_id, self.model.meta.program_id)
            lifted = root / "opt" / "cogos" / "usl-lifted"
            self.assertTrue(lifted.is_dir())
            expected = {
                "lifted_model.json",
                "law_bundle.json",
                "capability_lattice.json",
                "broker_profile.json",
                "gate_policy.json",
                "governance_decode_bundle.json",
            }
            for name in expected:
                path = lifted / name
                self.assertTrue(path.is_file(), msg=name)
                json.loads(path.read_text(encoding="utf-8"))

    def test_forge_compiler_static_requires_rootfs(self) -> None:
        with self.assertRaises(ValueError):
            ForgeCompiler.emit(self.model, mode="static", law=self.law)


if __name__ == "__main__":
    unittest.main()
