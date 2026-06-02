"""Lab Console HTTP route tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


class TestLabHttpRoutes(unittest.TestCase):
    def test_lab_init_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = Path(__file__).resolve().parents[1] / "lab" / "specs" / "default.yaml"
            client = TestClient(app)
            init = client.post(
                "/v1/lab/projects",
                json={
                    "project_id": "http-lab-test",
                    "spec": str(spec_path),
                    "source": ".",
                    "runtime_root": tmp,
                },
            )
            self.assertEqual(init.status_code, 200, init.text)
            status = client.get(f"/v1/lab/projects/http-lab-test/status?runtime_root={tmp}")
            self.assertEqual(status.status_code, 200)
            self.assertEqual(status.json()["project_id"], "http-lab-test")


if __name__ == "__main__":
    unittest.main()
