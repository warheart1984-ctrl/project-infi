"""Tests for identity self-model observation (ICC-0)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.identity_self_model_registry import validate_identity_registry
from src.identity_self_model_runtime import IdentitySelfModelRuntime, validate_claim_against_anchor


class IdentitySelfModelObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_identity_registry.v1.json",
            gov / "operator_identity_registry.v1.json",
        )
        self.runtime = IdentitySelfModelRuntime(
            runtime_dir=Path(self._tmpdir.name),
            repo_root=root,
        )
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_identity_registry_valid(self):
        self.assertEqual(validate_identity_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_surfaces_candidates_without_foundation_write(self):
        result = self.runtime.observe_identity_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("icc_class"), "ICC-0")
        self.assertGreaterEqual(result.get("candidate_count"), 1)
        self.assertFalse(self.runtime._foundation_path.is_file())

    def test_anchor_validation_rejects_forbidden_claim(self):
        bad = {
            "statement": "Enable identity_mutation without operator",
            "claim_kind": "doctrine",
        }
        validation = validate_claim_against_anchor(bad)
        self.assertFalse(validation.get("aligned"))
        self.assertTrue(validation.get("violations"))

    def test_identity_api_observe(self):
        res = self.client.post(
            "/api/operator/identity/observe",
            data=json.dumps({"window_days": 30}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("outcome"), "observed")

    def test_identity_api_get(self):
        res = self.client.get("/api/operator/identity")
        self.assertEqual(res.status_code, 200)
        self.assertIn("posture", res.get_json())


if __name__ == "__main__":
    unittest.main()
