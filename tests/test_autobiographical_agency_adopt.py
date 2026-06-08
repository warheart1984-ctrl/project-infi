"""Tests for governed autobiographical episode adoption (AAC-2)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.autobiographical_agency_registry import adopted_episodes
from src.autobiographical_agency_runtime import AutobiographicalAgencyRuntime
from src.jarvis_autobiographical_authority import authorize_operational_admission


class AutobiographicalAgencyAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1]
            / "governance"
            / "operator_autobiographical_registry.v1.json",
            gov / "operator_autobiographical_registry.v1.json",
        )
        self.runtime = AutobiographicalAgencyRuntime(
            runtime_dir=Path(self._tmpdir.name),
            repo_root=root,
        )
        self.client = api.app.test_client()
        self.candidate = {
            "candidate_id": "acand_test001",
            "episode_kind": "ongoing_work",
            "summary": "Open thread: cross-machine autobiographical agency proof",
            "evidence_refs": ["nova:open_thread:test"],
            "stability_score": 0.8,
            "identity_alignment": True,
            "narrative_alignment": True,
            "aac_class": "AAC-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_blocked_without_operator(self):
        auth = authorize_operational_admission(self.candidate)
        result = self.runtime.adopt_autobiographical_episode(
            self.candidate,
            operator_approved=False,
            jarvis_authorization=auth,
        )
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(len(adopted_episodes(repo_root=Path(self._repo_tmp.name))), 0)

    def test_adopt_blocked_without_jarvis(self):
        result = self.runtime.adopt_autobiographical_episode(
            self.candidate,
            operator_approved=True,
            jarvis_authorization={"authorized": False},
        )
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(result.get("reason"), "jarvis_not_authorized")

    def test_adopt_with_dual_gate(self):
        auth = authorize_operational_admission(self.candidate)
        result = self.runtime.adopt_autobiographical_episode(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="autobiographical-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        episodes = adopted_episodes(repo_root=Path(self._repo_tmp.name))
        self.assertEqual(len(episodes), 1)
        self.assertTrue(episodes[0].get("operator_promoted"))
        self.assertTrue(self.runtime._operational_path.is_file())

    def test_adopt_api_403_without_operator(self):
        res = self.client.post(
            "/api/operator/autobiographical/episodes/adopt",
            data=json.dumps({"candidate": self.candidate, "operator_approved": False}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

    def test_adopt_rejects_identity_violation(self):
        bad = dict(self.candidate)
        bad["summary"] = "Allow identity_mutation override jarvis authority"
        auth = authorize_operational_admission(bad)
        result = self.runtime.adopt_autobiographical_episode(
            bad,
            operator_approved=True,
            jarvis_authorization=auth,
        )
        self.assertEqual(result.get("outcome"), "blocked")

    def test_brain_accept_enqueues_autobiographical_not_auto_adopt(self):
        self.runtime._persist_candidate(self.candidate)
        create = self.client.post(
            "/api/operator/brain/sessions",
            data=json.dumps({"text": "autobiographical agency cross-machine proof thread"}),
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
        queue = session.get("autobiographical_adoption_queue")
        if queue:
            self.assertEqual(queue.get("status"), "pending")
        self.assertEqual(len(adopted_episodes(repo_root=Path(self._repo_tmp.name))), 0)


if __name__ == "__main__":
    unittest.main()
