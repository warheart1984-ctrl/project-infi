"""Tests for inter-substrate diplomacy observation (ISD-0)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.diplomacy.registry import validate_diplomatic_registry
from src.diplomacy.runtime import InterSubstrateDiplomacyRuntime


class InterSubstrateDiplomacyObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_diplomatic_registry.v1.json",
            gov / "operator_diplomatic_registry.v1.json",
        )
        self.runtime = InterSubstrateDiplomacyRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_registry_valid(self):
        self.assertEqual(validate_diplomatic_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_without_overlay_write(self):
        result = self.runtime.observe_substrate_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("isd_class"), "ISD-0")
        self.assertFalse(self.runtime._overlay_path.is_file())
        surfaces = result.get("charter_surfaces") or {}
        self.assertEqual(surfaces.get("epistemic_perimeter", {}).get("charter_article"), "IV")
        self.assertEqual(surfaces.get("collaboration_options", {}).get("charter_article"), "V")
        self.assertGreaterEqual(len(surfaces.get("collaboration_options", {}).get("options") or []), 2)

    def test_api_get(self):
        res = self.client.get("/api/operator/diplomacy")
        self.assertEqual(res.status_code, 200)
        body = res.get_json() or {}
        self.assertIn("charter_surfaces", body)


if __name__ == "__main__":
    unittest.main()
