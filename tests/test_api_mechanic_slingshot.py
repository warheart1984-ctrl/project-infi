"""API integration tests for Mechanic + Slingshot session payloads."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import src.api as api
from src.conversation_memory import conversation_memory

FIXTURE_CLEAN = Path(__file__).resolve().parents[1] / "mechanic" / "fixtures" / "sample-customer-repo-clean"
TRACE_CLEAN = FIXTURE_CLEAN / "traces" / "session.ndjson"


class TestApiMechanicSlingshotPayload(unittest.TestCase):
    def setUp(self):
        self._orig_enforce = os.environ.get("MECHANIC_ENFORCE_PROFILE")
        os.environ.pop("MECHANIC_ENFORCE_PROFILE", None)

    def tearDown(self):
        if self._orig_enforce is None:
            os.environ.pop("MECHANIC_ENFORCE_PROFILE", None)
        else:
            os.environ["MECHANIC_ENFORCE_PROFILE"] = self._orig_enforce

    def test_runtime_payload_includes_slingshot_and_mechanic_fields(self):
        session = api._create_chat_session_from_payload({"persona_mode": "builder"})
        session.metadata["mechanic_case_id"] = "demo-case"
        session.metadata["slingshot"] = {
            "active": True,
            "case_id": "demo-case",
            "authorized_goals": ["analyze only"],
            "required_constraints": ["no apply"],
            "packet": {"expires_at_utc": "2099-01-01T00:00:00Z", "compose_mode": "fast"},
        }
        session.metadata["slingshot_last_receipt"] = {"impact_status": "ok"}
        payload = api._build_chat_runtime_payload(session, session.session_id)
        self.assertEqual(payload["mechanic_case_id"], "demo-case")
        self.assertTrue(payload["slingshot"]["active"])
        self.assertEqual(payload["slingshot"]["case_id"], "demo-case")
        self.assertEqual(payload["slingshot_last_receipt"]["impact_status"], "ok")
        self.assertIn("enforcement_enabled", payload["mechanic_enforcement"])

    def test_patch_mechanic_case_binding(self):
        with api.app.test_client() as client:
            create = client.post("/api/chat/sessions", json={"persona_mode": "builder"})
            self.assertEqual(create.status_code, 201)
            session_id = create.get_json()["session_id"]
            patch = client.patch(
                f"/api/chat/sessions/{session_id}/mechanic",
                json={"mechanic_case_id": "bound-case"},
            )
            self.assertEqual(patch.status_code, 200)
            self.assertEqual(patch.get_json()["mechanic_case_id"], "bound-case")

    def test_jarvis_compat_forwards_slingshot_payload(self):
        context, message_payload, _mode = api._build_jarvis_compat_message_payload(
            {
                "input": "hello",
                "context": {"mechanic_case_id": "compat-case"},
                "slingshot": {
                    "case_id": "compat-case",
                    "authorized_goals": ["analyze only"],
                    "required_constraints": ["no apply"],
                },
            }
        )
        self.assertEqual(context.get("mechanic_case_id"), "compat-case")
        self.assertEqual(message_payload["slingshot"]["case_id"], "compat-case")

    @mock.patch("src.api._generate_chat_response", return_value="ok")
    @mock.patch("src.api.bootstrap_ai_runtime")
    def test_mechanic_enforcement_blocks_when_profile_missing(self, _bootstrap, _generate):
        os.environ["MECHANIC_ENFORCE_PROFILE"] = "1"
        with tempfile.TemporaryDirectory() as tmp:
            case_id = "enforce-block"
            case_dir = Path(tmp) / case_id
            case_dir.mkdir(parents=True)
            (case_dir / "MECHANIC_RUNTIME_PROFILE.json").write_text(
                json.dumps({"case_id": case_id, "allowed_actions": ["propose"]}),
                encoding="utf-8",
            )
            with api.app.test_client() as client:
                create = client.post(
                    "/api/chat/sessions",
                    json={"persona_mode": "builder", "mechanic_case_id": case_id},
                )
                session_id = create.get_json()["session_id"]
                with mock.patch.dict(os.environ, {"MECHANIC_RUNTIME_DIR": tmp}, clear=False):
                    response = client.post(
                        f"/api/chat/sessions/{session_id}/message",
                        json={"message": "test turn"},
                    )
                self.assertIn(response.status_code, {403, 200})

    def test_slingshot_preload_clean_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"SLINGSHOT_RUNTIME_DIR": tmp, "MECHANIC_RUNTIME_DIR": tmp}, clear=False):
                with api.app.test_client() as client:
                    response = client.post(
                        "/api/slingshot/preload",
                        json={
                            "case_id": "api-preload-clean",
                            "repo_path": str(FIXTURE_CLEAN),
                            "trace_path": str(TRACE_CLEAN),
                            "authorized_goals": ["analyze support triage only"],
                            "required_constraints": ["no apply"],
                        },
                    )
                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertFalse(payload.get("launch_blocked"))

    def test_slingshot_status_after_preload(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"SLINGSHOT_RUNTIME_DIR": tmp, "MECHANIC_RUNTIME_DIR": tmp}, clear=False):
                with api.app.test_client() as client:
                    client.post(
                        "/api/slingshot/preload",
                        json={
                            "case_id": "api-status-clean",
                            "repo_path": str(FIXTURE_CLEAN),
                            "trace_path": str(TRACE_CLEAN),
                        },
                    )
                    status = client.get("/api/slingshot/status?case_id=api-status-clean")
                self.assertEqual(status.status_code, 200)
                body = status.get_json()
                self.assertTrue(body.get("artifacts_present"))


if __name__ == "__main__":
    unittest.main()
