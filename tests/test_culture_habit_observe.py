"""Tests for culture habit observation (HCC-0)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.culture_habit_runtime import CultureHabitRuntime
from src.culture_habit_registry import validate_habit_registry
from src.operator_decision_ledger import append_organ_handoff_event


class CultureHabitObserveTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        os.environ["AAIS_CULTURE_HABIT_MIN_OCCURRENCE"] = "2"
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_habit_registry.v1.json",
            gov / "operator_habit_registry.v1.json",
        )
        self.runtime = CultureHabitRuntime(
            runtime_dir=Path(self._tmpdir.name),
            repo_root=root,
        )
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("AAIS_CULTURE_HABIT_MIN_OCCURRENCE", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_habit_registry_valid(self):
        self.assertEqual(validate_habit_registry(repo_root=Path(self._repo_tmp.name)), [])

    def test_mine_from_ledger_handoffs(self):
        handoff = {
            "source_family_id": "knowledge_work",
            "target_family_id": "creative_workflows",
            "source_chain_id": "research_brief",
            "chain_id": "creative_asset_package",
        }
        for _ in range(3):
            append_organ_handoff_event("global", handoff=handoff, mesh_run_id="mesh_test123")
        result = self.runtime.mine_habit_patterns()
        self.assertEqual(result.get("outcome"), "observed")
        self.assertGreaterEqual(result.get("candidate_count"), 1)

    def test_culture_api_observe(self):
        res = self.client.post(
            "/api/operator/culture/observe",
            data=json.dumps({"window_days": 30}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("outcome"), "observed")

    def test_culture_api_get(self):
        res = self.client.get("/api/operator/culture")
        self.assertEqual(res.status_code, 200)
        self.assertIn("posture", res.get_json())


if __name__ == "__main__":
    unittest.main()
