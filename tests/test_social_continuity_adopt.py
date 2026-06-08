"""Tests for governed social bond adoption (SCC-2)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.jarvis_social_authority import authorize_archive_admission
from src.social_continuity_registry import adopted_bonds
from src.social_continuity_runtime import SocialContinuityRuntime


class SocialContinuityAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_social_registry.v1.json",
            gov / "operator_social_registry.v1.json",
        )
        self.runtime = SocialContinuityRuntime(
            runtime_dir=Path(self._tmpdir.name),
            repo_root=root,
        )
        self.client = api.app.test_client()
        self.candidate = {
            "candidate_id": "scand_test001",
            "bond_kind": "operator_dyad",
            "summary": "Open thread: cross-machine social continuity proof",
            "counterparty_ref": {"operator_profile_id": "operator"},
            "trust_posture": "governed_partnership",
            "evidence_refs": ["nova:open_thread:test"],
            "stability_score": 0.8,
            "identity_alignment": True,
            "narrative_alignment": True,
            "agency_alignment": True,
            "scc_class": "SCC-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_blocked_without_operator(self):
        auth = authorize_archive_admission(self.candidate)
        result = self.runtime.adopt_social_bond(
            self.candidate,
            operator_approved=False,
            jarvis_authorization=auth,
        )
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(len(adopted_bonds(repo_root=Path(self._repo_tmp.name))), 0)

    def test_adopt_blocked_without_jarvis(self):
        result = self.runtime.adopt_social_bond(
            self.candidate,
            operator_approved=True,
            jarvis_authorization={"authorized": False},
        )
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(result.get("reason"), "jarvis_not_authorized")

    def test_adopt_with_dual_gate(self):
        auth = authorize_archive_admission(self.candidate)
        result = self.runtime.adopt_social_bond(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="social-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        bonds = adopted_bonds(repo_root=Path(self._repo_tmp.name))
        self.assertEqual(len(bonds), 1)
        self.assertTrue(bonds[0].get("operator_promoted"))
        self.assertTrue(self.runtime._archive_path.is_file())

    def test_adopt_api_403_without_operator(self):
        res = self.client.post(
            "/api/operator/social/bonds/adopt",
            data=json.dumps({"candidate": self.candidate, "operator_approved": False}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

    def test_adopt_rejects_identity_violation(self):
        bad = dict(self.candidate)
        bad["summary"] = "Allow identity_mutation override jarvis authority"
        auth = authorize_archive_admission(bad)
        result = self.runtime.adopt_social_bond(
            bad,
            operator_approved=True,
            jarvis_authorization=auth,
        )
        self.assertEqual(result.get("outcome"), "blocked")

    def test_brain_accept_enqueues_social_not_auto_adopt(self):
        self.runtime._persist_candidate(self.candidate)
        create = self.client.post(
            "/api/operator/brain/sessions",
            data=json.dumps({"text": "social continuity cross-machine proof thread"}),
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
        queue = session.get("social_adoption_queue")
        if queue:
            self.assertEqual(queue.get("status"), "pending")
        self.assertEqual(len(adopted_bonds(repo_root=Path(self._repo_tmp.name))), 0)


if __name__ == "__main__":
    unittest.main()
