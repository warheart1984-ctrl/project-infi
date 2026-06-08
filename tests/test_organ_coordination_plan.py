"""Tests for organ mesh planning (OCC-0)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

import src.api as api
from src.organ_coordination_runtime import OrganCoordinationRuntime
from src.workflow_family_registry import list_handoff_edges, validate_handoff_graph


class OrganCoordinationPlanTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.runtime = OrganCoordinationRuntime(runtime_dir=__import__("pathlib").Path(self._tmpdir.name))
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_handoff_graph_valid(self):
        errors = validate_handoff_graph()
        self.assertEqual(errors, [])
        edges = list_handoff_edges()
        self.assertGreaterEqual(len(edges), 4)

    def test_plan_from_intent(self):
        plan = self.runtime.plan_mesh_run(intent_text="research brief creative workflow")
        self.assertIn(plan.get("outcome"), {"planned", "blocked"})
        self.assertIn("steps", plan)
        self.assertEqual(len(plan.get("steps") or []), 2)

    def test_mesh_api_get(self):
        res = self.client.get("/api/operator/organs/mesh")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get("graph_valid"))
        self.assertGreaterEqual(body.get("edge_count"), 4)

    def test_mesh_plan_api(self):
        res = self.client.post(
            "/api/operator/organs/mesh/plan",
            data=json.dumps({"intent_text": "data cleanup research brief"}),
            content_type="application/json",
        )
        self.assertIn(res.status_code, {200, 400})
        plan = res.get_json()
        self.assertIn("steps", plan)


if __name__ == "__main__":
    unittest.main()
