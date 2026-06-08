"""Tests for multi-being continuity observation (MBC-0)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.multi_being_continuity_registry import validate_multi_being_registry
from src.multi_being_continuity_runtime import (
    MultiBeingContinuityRuntime,
    validate_pact_against_identity_narrative_agency_and_social,
)


class MultiBeingContinuityObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_multi_being_registry.v1.json",
            gov / "operator_multi_being_registry.v1.json",
        )
        self.runtime = MultiBeingContinuityRuntime(
            runtime_dir=Path(self._tmpdir.name),
            repo_root=root,
        )
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_multi_being_registry_valid(self):
        self.assertEqual(validate_multi_being_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_surfaces_candidates_without_federation_write(self):
        result = self.runtime.observe_multi_being_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("mbc_class"), "MBC-0")
        self.assertGreaterEqual(result.get("candidate_count"), 0)
        self.assertFalse(self.runtime._federation_path.is_file())

    def test_pact_validation_rejects_forbidden_summary(self):
        bad = {"summary": "Enable identity_mutation override jarvis", "pact_kind": "bilateral_organism"}
        validation = validate_pact_against_identity_narrative_agency_and_social(bad)
        self.assertFalse(validation.get("aligned"))

    def test_multi_being_api_observe(self):
        res = self.client.post(
            "/api/operator/multi-being/observe",
            data=json.dumps({"window_days": 30}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("outcome"), "observed")

    def test_multi_being_api_get(self):
        res = self.client.get("/api/operator/multi-being")
        self.assertEqual(res.status_code, 200)
        self.assertIn("posture", res.get_json())


if __name__ == "__main__":
    unittest.main()
