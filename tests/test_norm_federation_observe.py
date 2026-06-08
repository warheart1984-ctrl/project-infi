"""Tests for norm federation observation (NFD-0)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.norm_federation_registry import validate_norm_federation_registry
from src.norm_federation_runtime import NormFederationRuntime


class NormFederationObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_norm_federation_registry.v1.json",
            gov / "operator_norm_federation_registry.v1.json",
        )
        self.runtime = NormFederationRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_registry_valid(self):
        self.assertEqual(validate_norm_federation_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_without_overlay_write(self):
        result = self.runtime.observe_federation_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("nfd_class"), "NFD-0")
        self.assertFalse(self.runtime._overlay_path.is_file())
        surfaces = result.get("charter_surfaces") or {}
        self.assertEqual(surfaces.get("epistemic_perimeter", {}).get("charter_article"), "IV")
        self.assertEqual(surfaces.get("collaboration_options", {}).get("charter_article"), "V")
        self.assertGreaterEqual(len(surfaces.get("collaboration_options", {}).get("options") or []), 2)

    def test_api_get(self):
        res = self.client.get("/api/operator/norm-federations")
        self.assertEqual(res.status_code, 200)
        body = res.get_json() or {}
        self.assertIn("charter_surfaces", body)


if __name__ == "__main__":
    unittest.main()
