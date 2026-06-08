"""Tests for governed habit adoption (HCC-2)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.culture_habit_registry import adopted_habits
from src.culture_habit_runtime import CultureHabitRuntime


class CultureHabitAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
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
        self.candidate = {
            "candidate_id": "cand_test001",
            "pattern_kind": "mesh_path",
            "pattern_key": "mesh_path:knowledge_work:creative_workflows:research_brief:creative_asset_package",
            "source_family_id": "knowledge_work",
            "target_family_id": "creative_workflows",
            "chain_ids": ["research_brief", "creative_asset_package"],
            "occurrence_count": 5,
            "hcc_class": "HCC-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_blocked_without_operator(self):
        result = self.runtime.adopt_habit(self.candidate, operator_approved=False)
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(len(adopted_habits(repo_root=Path(self._repo_tmp.name))), 0)

    def test_adopt_with_operator(self):
        result = self.runtime.adopt_habit(self.candidate, operator_approved=True, session_id="habit-test")
        self.assertEqual(result.get("outcome"), "adopted")
        habits = adopted_habits(repo_root=Path(self._repo_tmp.name))
        self.assertEqual(len(habits), 1)
        self.assertTrue(habits[0].get("operator_promoted"))

    def test_adopt_api_403_without_operator(self):
        res = self.client.post(
            "/api/operator/culture/habits/adopt",
            data=json.dumps({"candidate": self.candidate, "operator_approved": False}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

    def test_mesh_habit_boost_after_adopt(self):
        self.runtime.adopt_habit(self.candidate, operator_approved=True)
        edge = {
            "source_family_id": "knowledge_work",
            "target_family_id": "creative_workflows",
            "source_chain_id": "research_brief",
            "chain_id": "creative_asset_package",
        }
        boost = self.runtime.mesh_habit_boost(edge)
        self.assertGreater(boost, 0.0)

    def test_brain_accept_enqueues_habit_not_auto_adopt(self):
        self.runtime._persist_candidate(self.candidate)
        create = self.client.post(
            "/api/operator/brain/sessions",
            data=json.dumps({"text": "research brief creative asset"}),
            content_type="application/json",
        )
        self.assertEqual(create.status_code, 201)
        session_id = create.get_json()["session"]["session_id"]
        decide = self.client.post(
            f"/api/operator/brain/sessions/{session_id}/decide",
            data=json.dumps({"decision": "accept"}),
            content_type="application/json",
        )
        self.assertEqual(decide.status_code, 200)
        session = decide.get_json()["session"]
        queue = session.get("habit_adoption_queue")
        if queue:
            self.assertEqual(queue.get("status"), "pending")
        self.assertEqual(len(adopted_habits(repo_root=Path(self._repo_tmp.name))), 0)


if __name__ == "__main__":
    unittest.main()
