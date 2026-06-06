"""Operator workflow API smoke tests."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import src.api as api


class OperatorWorkflowApiTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.client = api.app.test_client()

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_plugins_libraries(self):
        res = self.client.get("/api/operator/plugins/libraries")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.get_json()["libraries"]), 50)

    def test_organs_and_brain(self):
        organs = self.client.get("/api/operator/organs")
        self.assertEqual(organs.status_code, 200)
        self.assertEqual(organs.get_json()["count"], 6)
        brain = self.client.post(
            "/api/operator/brain/sessions",
            data=json.dumps({"text": "research brief"}),
            content_type="application/json",
        )
        self.assertEqual(brain.status_code, 201)


if __name__ == "__main__":
    unittest.main()
