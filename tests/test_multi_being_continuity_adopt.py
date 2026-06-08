"""Tests for governed multi-being pact adoption (MBC-2)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.jarvis_multi_being_authority import authorize_federation_slot_admission
from src.multi_being_continuity_registry import adopted_pacts
from src.multi_being_continuity_runtime import MultiBeingContinuityRuntime


class MultiBeingContinuityAdoptTests(unittest.TestCase):
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
        self.candidate = {
            "candidate_id": "mcand_test001",
            "pact_kind": "bilateral_organism",
            "summary": "Open thread: cross-organism multi-being continuity proof",
            "counterparty_organism_ref": {"tenant_id": "peer-tenant", "organism_id": "peer-org"},
            "continuity_posture": "governed_bilateral",
            "trust_tier": "governed_bilateral",
            "evidence_refs": ["nova:open_thread:test"],
            "stability_score": 0.8,
            "identity_alignment": True,
            "narrative_alignment": True,
            "agency_alignment": True,
            "social_alignment": True,
            "mbc_class": "MBC-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_blocked_without_operator(self):
        auth = authorize_federation_slot_admission(self.candidate)
        result = self.runtime.adopt_multi_being_pact(
            self.candidate,
            operator_approved=False,
            jarvis_authorization=auth,
        )
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(len(adopted_pacts(repo_root=Path(self._repo_tmp.name))), 0)

    def test_adopt_blocked_without_jarvis(self):
        result = self.runtime.adopt_multi_being_pact(
            self.candidate,
            operator_approved=True,
            jarvis_authorization={"authorized": False},
        )
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(result.get("reason"), "jarvis_not_authorized")

    def test_adopt_with_dual_gate(self):
        auth = authorize_federation_slot_admission(self.candidate)
        result = self.runtime.adopt_multi_being_pact(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="multi-being-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        pacts = adopted_pacts(repo_root=Path(self._repo_tmp.name))
        self.assertEqual(len(pacts), 1)
        self.assertTrue(pacts[0].get("operator_promoted"))
        self.assertTrue(self.runtime._federation_path.is_file())

    def test_adopt_api_403_without_operator(self):
        res = self.client.post(
            "/api/operator/multi-being/pacts/adopt",
            data=json.dumps({"candidate": self.candidate, "operator_approved": False}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 403)

    def test_adopt_rejects_identity_violation(self):
        bad = dict(self.candidate)
        bad["summary"] = "Allow identity_mutation override jarvis authority"
        auth = authorize_federation_slot_admission(bad)
        result = self.runtime.adopt_multi_being_pact(
            bad,
            operator_approved=True,
            jarvis_authorization=auth,
        )
        self.assertEqual(result.get("outcome"), "blocked")

    def test_brain_accept_enqueues_multi_being_not_auto_adopt(self):
        self.runtime._persist_candidate(self.candidate)
        create = self.client.post(
            "/api/operator/brain/sessions",
            data=json.dumps({"text": "multi-being continuity cross-organism proof thread"}),
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
        queue = session.get("multi_being_adoption_queue")
        if queue:
            self.assertEqual(queue.get("status"), "pending")
        self.assertEqual(len(adopted_pacts(repo_root=Path(self._repo_tmp.name))), 0)


if __name__ == "__main__":
    unittest.main()
