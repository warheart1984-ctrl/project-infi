from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.cloud_forge.types import LawEnvelope
from src.usl.exo.courier import ExokernelCourier
from src.usl.exo.registry import AAISRegistry, FileArtifactStore, SqliteArtifactStore
from tests.fixtures.usl.build_fixtures import ensure_fixtures


class AAISRegistryPersistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.elf_path, _ = ensure_fixtures()

    def test_file_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FileArtifactStore(Path(tmp))
            registry_a = AAISRegistry(store=store)
            courier = ExokernelCourier(registry=registry_a)
            raw = Path(self.elf_path).read_bytes()
            law = LawEnvelope(law_id="test-law", law_version="9")
            result = courier.lift_and_register(
                raw,
                source_path=str(self.elf_path),
                domain="test-domain",
                law_envelope=law,
            )

            registry_b = AAISRegistry(store=store)
            record = registry_b.get_artifact(result.artifact_id)
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.program_id, result.model.meta.program_id)
            self.assertEqual(record.slice_id, "test-domain")

            model = registry_b.get_lifted_model(result.artifact_id)
            self.assertIsNotNone(model)
            assert model is not None
            self.assertEqual(model.meta.program_id, result.model.meta.program_id)
            self.assertEqual(len(model.control.blocks), len(result.model.control.blocks))

            graph = registry_b.get_engine_graph(result.artifact_id)
            self.assertIsNotNone(graph)
            assert graph is not None
            self.assertEqual(graph.program_id, result.model.meta.program_id)

            envelope = registry_b.get_law_envelope(result.artifact_id)
            self.assertIsNotNone(envelope)
            assert envelope is not None
            self.assertEqual(envelope.law_id, "test-law")
            self.assertEqual(envelope.law_version, "9")

    def test_list_by_domain_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FileArtifactStore(Path(tmp))
            registry = AAISRegistry(store=store)
            courier = ExokernelCourier(registry=registry)
            raw = Path(self.elf_path).read_bytes()

            r1 = courier.lift_and_register(raw, domain="alpha", source_path=str(self.elf_path))
            r2 = courier.lift_and_register(raw, domain="beta", source_path=str(self.elf_path))

            alpha = registry.list_by_domain("alpha")
            self.assertEqual(len(alpha), 1)
            self.assertEqual(alpha[0].artifact_id, r1.artifact_id)

            all_records = registry.list_by_domain(None)
            self.assertEqual(len(all_records), 2)
            ids = {rec.artifact_id for rec in all_records}
            self.assertIn(r1.artifact_id, ids)
            self.assertIn(r2.artifact_id, ids)

    def test_sqlite_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "registry.db"
            store = SqliteArtifactStore(db_path)
            registry_a = AAISRegistry(store=store)
            courier = ExokernelCourier(registry=registry_a)
            raw = Path(self.elf_path).read_bytes()
            law = LawEnvelope(law_id="sqlite-law", law_version="1")
            result = courier.lift_and_register(
                raw,
                source_path=str(self.elf_path),
                domain="sqlite-domain",
                law_envelope=law,
            )

            registry_b = AAISRegistry(store=SqliteArtifactStore(db_path))
            record = registry_b.get_artifact(result.artifact_id)
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.slice_id, "sqlite-domain")

            model = registry_b.get_lifted_model(result.artifact_id)
            self.assertIsNotNone(model)
            assert model is not None
            self.assertEqual(model.meta.program_id, result.model.meta.program_id)


if __name__ == "__main__":
    unittest.main()
