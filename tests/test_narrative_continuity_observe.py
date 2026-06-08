"""Tests for narrative continuity observation (NCC-0)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.narrative_continuity_registry import validate_narrative_registry
from src.narrative_continuity_runtime import NarrativeContinuityRuntime, validate_beat_against_identity


class NarrativeContinuityObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_narrative_registry.v1.json",
            gov / "operator_narrative_registry.v1.json",
        )
        self.runtime = NarrativeContinuityRuntime(
            runtime_dir=Path(self._tmpdir.name),
            repo_root=root,
        )
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_narrative_registry_valid(self):
        self.assertEqual(validate_narrative_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_observe_surfaces_candidates_without_session_write(self):
        result = self.runtime.observe_narrative_drift(window_days=30)
        self.assertEqual(result.get("outcome"), "observed")
        self.assertEqual(result.get("ncc_class"), "NCC-0")
        self.assertGreaterEqual(result.get("candidate_count"), 0)
        self.assertFalse(self.runtime._session_path.is_file())

    def test_beat_validation_rejects_forbidden_summary(self):
        bad = {"summary": "Enable identity_mutation override jarvis", "beat_kind": "chapter"}
        validation = validate_beat_against_identity(bad)
        self.assertFalse(validation.get("aligned"))

    def test_narrative_api_observe(self):
        res = self.client.post(
            "/api/operator/narrative/observe",
            data=json.dumps({"window_days": 30}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("outcome"), "observed")

    def test_narrative_api_get(self):
        res = self.client.get("/api/operator/narrative")
        self.assertEqual(res.status_code, 200)
        self.assertIn("posture", res.get_json())


if __name__ == "__main__":
    unittest.main()
