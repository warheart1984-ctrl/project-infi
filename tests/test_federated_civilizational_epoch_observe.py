"""Tests for federated civilizational epoch observation (FCE-0)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.federated_civilizational_epoch_registry import validate_federated_epoch_registry
from src.federated_civilizational_epoch_runtime import FederatedCivilizationalEpochRuntime
from src.governed_civilization_registry import save_adopted_civilization


class FederatedCivilizationalEpochObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        repo_root = Path(__file__).resolve().parents[1]
        shutil.copy(
            repo_root / "governance" / "operator_federated_epoch_registry.v1.json",
            gov / "operator_federated_epoch_registry.v1.json",
        )
        shutil.copy(
            repo_root / "governance" / "operator_civilization_registry.v1.json",
            gov / "operator_civilization_registry.v1.json",
        )
        save_adopted_civilization(
            {
                "civilization_id": "gcv_seed001",
                "summary": "Seed governed civilization for FCE upstream",
                "admitted_charter_ids": ["charter_a", "charter_b"],
            },
            repo_root=root,
        )
        self.runtime = FederatedCivilizationalEpochRuntime(
            runtime_dir=Path(self._tmpdir.name), repo_root=root
        )
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("AAIS_POPULATION_FIXTURE_N", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_registry_valid(self):
        self.assertEqual(validate_federated_epoch_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_without_overlay_write(self):
        result = self.runtime.observe_epoch_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("fce_class"), "FCE-0")
        self.assertFalse(self.runtime._overlay_path.is_file())

    def test_population_fixture_reflected(self):
        os.environ["AAIS_POPULATION_FIXTURE_N"] = "42"
        result = self.runtime.observe_epoch_drift(window_days=7)
        self.assertEqual(result.get("population_member_count"), 42)

    def test_api_get(self):
        res = self.client.get("/api/operator/federated-epochs")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
