"""Tests for governed organ mesh execution."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.jarvis_organ_mesh_authority import authorize_mesh_run
from src.organ_coordination_runtime import OrganCoordinationRuntime


class OrganCoordinationExecuteTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.runtime = OrganCoordinationRuntime(runtime_dir=__import__("pathlib").Path(self._tmpdir.name))
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_jarvis_blocks_unauthorized_mesh(self):
        plan = self.runtime.plan_mesh_run(
            source_family_id="knowledge_work",
            handoff_edge_index=0,
        )
        if plan.get("outcome") != "planned":
            self.skipTest("plan blocked in this environment")
        run = self.runtime.execute_mesh_run(
            plan,
            operator_approved=True,
            dry_run=True,
            jarvis_authorization={"authorized": False},
        )
        self.assertEqual(run.get("reason"), "jarvis_not_authorized")

    def test_two_organ_dry_run_with_jarvis(self):
        plan = self.runtime.plan_mesh_run(
            source_family_id="knowledge_work",
            handoff_edge_index=0,
        )
        if plan.get("outcome") != "planned":
            self.skipTest("plan blocked in this environment")
        auth = authorize_mesh_run(plan, session_id="mesh-test")
        self.assertTrue(auth.get("authorized"))
        run = self.runtime.execute_mesh_run(
            plan,
            session_id="mesh-test",
            operator_approved=True,
            dry_run=True,
            jarvis_authorization=auth,
        )
        self.assertEqual(run.get("outcome"), "completed")
        self.assertGreaterEqual(len(run.get("handoffs") or []), 1)
        stored = self.runtime.get_run(str(run.get("run_id") or ""))
        self.assertIsNotNone(stored)

    def test_mesh_runs_api_403_without_jarvis(self):
        plan = self.runtime.plan_mesh_run(source_family_id="knowledge_work", handoff_edge_index=0)
        with patch("src.jarvis_organ_mesh_authority.authorize_mesh_run") as mock_auth:
            mock_auth.return_value = {"authorized": False, "reason": "verification_gate_rejected"}
            res = self.client.post(
                "/api/operator/organs/mesh/runs",
                data=json.dumps({"plan": plan, "operator_approved": True, "dry_run": True}),
                content_type="application/json",
            )
            self.assertEqual(res.status_code, 403)

    def test_brain_accept_enqueues_mesh_not_execute(self):
        create = self.client.post(
            "/api/operator/brain/sessions",
            data=json.dumps({"text": "research brief to creative asset package"}),
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
        queue = session.get("mesh_approval_queue")
        if queue:
            self.assertEqual(queue.get("status"), "pending")
        runs = self.runtime.list_runs()
        completed = [r for r in runs if r.get("status") == "completed"]
        self.assertEqual(len(completed), 0)


if __name__ == "__main__":
    unittest.main()
