"""Tests for constitutional ecosystem observation (CEC-0)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.constitutional_ecosystem_registry import validate_ecosystem_registry
from src.constitutional_ecosystem_runtime import ConstitutionalEcosystemRuntime


class ConstitutionalEcosystemObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_ecosystem_registry.v1.json",
            gov / "operator_ecosystem_registry.v1.json",
        )
        self.runtime = ConstitutionalEcosystemRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_registry_valid(self):
        self.assertEqual(validate_ecosystem_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_without_overlay_write(self):
        result = self.runtime.observe_ecosystem_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("cec_class"), "CEC-0")
        self.assertFalse(self.runtime._overlay_path.is_file())

    def test_api_get(self):
        res = self.client.get("/api/operator/ecosystems")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
