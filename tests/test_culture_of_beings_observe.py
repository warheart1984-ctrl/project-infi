"""Tests for culture-of-beings observation (COB-0)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.culture_of_beings_registry import validate_culture_of_beings_registry
from src.culture_of_beings_runtime import CultureOfBeingsRuntime, validate_norm_against_identity_narrative_agency_social_and_pacts


class CultureOfBeingsObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_culture_of_beings_registry.v1.json",
            gov / "operator_culture_of_beings_registry.v1.json",
        )
        self.runtime = CultureOfBeingsRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_registry_valid(self):
        self.assertEqual(validate_culture_of_beings_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_without_overlay_write(self):
        result = self.runtime.observe_culture_of_beings_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("cob_class"), "COB-0")
        self.assertFalse(self.runtime._overlay_path.is_file())

    def test_norm_validation_rejects_forbidden(self):
        bad = {"summary": "Enable identity_mutation override jarvis", "norm_kind": "handoff_ritual"}
        self.assertFalse(validate_norm_against_identity_narrative_agency_social_and_pacts(bad).get("aligned"))

    def test_api_observe(self):
        res = self.client.post(
            "/api/operator/culture-of-beings/observe",
            data=json.dumps({"window_days": 30}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json().get("outcome"), "observed")

    def test_api_get(self):
        res = self.client.get("/api/operator/culture-of-beings")
        self.assertEqual(res.status_code, 200)
        self.assertIn("posture", res.get_json())


if __name__ == "__main__":
    unittest.main()
