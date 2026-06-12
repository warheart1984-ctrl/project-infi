from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import json

from src.usl.exo.courier import ExokernelCourier
from src.usl.exo.registry import AAISRegistry
from src.usl.forge.bootstrap import bootstrap_forge_runtime
from src.usl.forge.dynamic_emitter import DynamicForgeBundle
from src.usl.forge.static_emitter import StaticForgeImageRef
from tests.fixtures.usl.build_fixtures import ensure_fixtures, ensure_windows_syscall_pe


class ExokernelCourierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, cls.pe_path = ensure_fixtures()
        cls.syscall_pe_path = ensure_windows_syscall_pe()

    def test_lift_and_register_dynamic(self) -> None:
        registry = AAISRegistry()
        courier = ExokernelCourier(registry=registry)
        raw = Path(self.elf_path).read_bytes()
        result = courier.lift_and_register(raw, source_path=str(self.elf_path))

        self.assertEqual(result.model.meta.program_id, result.guest.ubo.binary_id)
        self.assertIsInstance(result.forge_output, DynamicForgeBundle)
        self.assertTrue(result.artifact_id.startswith("aais-lift-"))
        record = registry.get_artifact(result.artifact_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.program_id, result.model.meta.program_id)
        graph = registry.get_engine_graph(result.artifact_id)
        self.assertIsNotNone(graph)
        assert graph is not None
        self.assertGreater(len(graph.nodes), 0)

    def test_lift_and_register_static(self) -> None:
        registry = AAISRegistry()
        courier = ExokernelCourier(registry=registry)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = courier.lift_and_register(
                Path(self.elf_path).read_bytes(),
                source_path=str(self.elf_path),
                forge_mode="static",
                rootfs_dir=root,
            )
            self.assertIsInstance(result.forge_output, StaticForgeImageRef)
            lifted = root / "opt" / "cogos" / "usl-lifted" / "lifted_model.json"
            self.assertTrue(lifted.is_file())

    def test_lift_and_register_from_path(self) -> None:
        registry = AAISRegistry()
        result = ExokernelCourier.lift_and_register_from_path(
            self.elf_path,
            registry=registry,
        )
        self.assertIsInstance(result.forge_output, DynamicForgeBundle)

    def test_lift_and_register_pe_windows(self) -> None:
        registry = AAISRegistry()
        courier = ExokernelCourier(registry=registry)
        raw = Path(self.syscall_pe_path).read_bytes()
        result = courier.lift_and_register(raw, source_path=str(self.syscall_pe_path))

        self.assertEqual(result.model.meta.format, "pe")
        self.assertEqual(result.model.meta.os_family, "windows")
        self.assertEqual(result.model.meta.architecture, "x86_64")
        self.assertTrue(result.artifact_id.startswith("aais-lift-"))
        self.assertGreaterEqual(len(result.model.effects.syscalls), 1)
        record = registry.get_artifact(result.artifact_id)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.program_id, result.model.meta.program_id)

    def test_bootstrap_rejects_block_severity_admission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            courier = ExokernelCourier()
            courier.lift_and_register(
                Path(self.elf_path).read_bytes(),
                source_path=str(self.elf_path),
                forge_mode="static",
                rootfs_dir=root,
            )
            forge_dir = root / "opt" / "cogos" / "usl-lifted"
            gate_path = forge_dir / "gate_policy.json"
            model_path = forge_dir / "lifted_model.json"
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            gate["admission_invariants"] = list(
                gate.get("admission_invariants") or []
            ) + ["inv-block-test"]
            gate_path.write_text(json.dumps(gate), encoding="utf-8")
            model = json.loads(model_path.read_text(encoding="utf-8"))
            rules = list(model.get("invariants", {}).get("rules") or [])
            rules.append({"invariant_id": "inv-block-test", "severity": "block"})
            model["invariants"] = {"rules": rules}
            model_path.write_text(json.dumps(model), encoding="utf-8")
            with self.assertRaises(RuntimeError) as ctx:
                bootstrap_forge_runtime(
                    elf_path=Path(self.elf_path),
                    forge_dir=forge_dir,
                )
            self.assertIn("admission blocked", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
