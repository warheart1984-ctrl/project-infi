"""Health compatibility tests for the canonical FastAPI app."""

from __future__ import annotations

import types
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main as app_main


class TestCanonicalHealth(unittest.TestCase):
    def test_openapi_includes_shell_jarvis_route(self):
        paths = app_main.app.openapi()["paths"]

        self.assertIn("/api/jarvis", paths)
        self.assertIn("post", paths["/api/jarvis"])
        self.assertIn("/api/memory/write", paths)
        self.assertIn("post", paths["/api/memory/write"])
        self.assertNotIn("/chat", paths)
        self.assertNotIn("/chat/stream", paths)

    def test_shell_jarvis_route_proxies_to_legacy_runtime(self):
        with patch.object(
            app_main,
            "_forward_legacy_jarvis_request",
            return_value=(
                200,
                {
                    "output": "Jarvis received: hello",
                    "trace": None,
                    "status": "ok",
                    "session_id": "session-1",
                    "runtime": {"response": "Jarvis received: hello"},
                    "mode": "normal",
                },
            ),
        ) as mock_forward:
            with TestClient(app_main.app) as client:
                response = client.post("/api/jarvis", json={"input": "hello"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["output"], "Jarvis received: hello")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["session_id"], "session-1")
        mock_forward.assert_called_once_with({"input": "hello", "context": None, "mode": "normal"})

    def test_shell_memory_write_route_proxies_to_legacy_runtime(self):
        with patch.object(
            app_main,
            "_forward_legacy_runtime_json_request",
            return_value=(
                201,
                {
                    "id": "memory-1",
                    "text": "remember this",
                    "governance": {"action": "write"},
                },
            ),
        ) as mock_forward:
            with TestClient(app_main.app) as client:
                response = client.post("/api/memory/write", json={"text": "remember this"})

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["id"], "memory-1")
        self.assertEqual(payload["text"], "remember this")
        mock_forward.assert_called_once_with(
            "/api/jarvis/memory",
            {
                "text": "remember this",
                "tags": [],
                "source": None,
                "category": None,
                "kind": None,
                "why": None,
            },
        )

    def test_legacy_bridge_mount_uses_supported_a2wsgi_wrapper(self):
        mounted_route = next(
            route for route in app_main.app.routes if getattr(route, "path", None) == app_main.LEGACY_API_MOUNT_PATH
        )

        self.assertEqual(mounted_route.app.__class__.__name__, "WSGIMiddleware")
        self.assertTrue(mounted_route.app.__class__.__module__.startswith("a2wsgi"))

    def test_build_operator_health_payload_uses_legacy_runtime_snapshot(self):
        bootstrap_calls: list[str] = []

        fake_legacy_api = types.SimpleNamespace(
            bootstrap_ai_runtime=lambda reason="startup": bootstrap_calls.append(reason),
            _build_ai_runtime_status=lambda: {
                "requested_model_mode": "real",
                "active_model_mode": "real",
                "ai_status": "initialized",
                "ai_bootstrap_status": "initialized",
                "ai_bootstrap_reason": "run_api",
                "ai_fallback_active": False,
            },
            system_guard=types.SimpleNamespace(snapshot=lambda limit_events=4: {"status": "nominal"}),
            dreamspace=types.SimpleNamespace(snapshot=lambda limit_dreams=2: {"status": "stopped"}),
        )

        with patch("app.main.importlib.import_module", return_value=fake_legacy_api):
            payload = app_main._build_operator_health_payload()

        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["service"], "AAIS Multi-Modal AI")
        self.assertEqual(payload["active_model_mode"], "real")
        self.assertEqual(payload["ai_status"], "initialized")
        self.assertEqual(bootstrap_calls, [])
        self.assertIn("contractors", payload)
        self.assertEqual(len(payload["contractors"]), 3)

    def test_build_operator_health_payload_bootstraps_when_not_initialized(self):
        bootstrap_calls: list[tuple[str, bool]] = []

        def fake_bootstrap(*, reason="startup", prefer_real=False):
            bootstrap_calls.append((reason, prefer_real))

        fake_legacy_api = types.SimpleNamespace(
            bootstrap_ai_runtime=fake_bootstrap,
            _build_ai_runtime_status=lambda: {
                "requested_model_mode": "mock",
                "active_model_mode": "mock",
                "ai_status": "not_initialized",
                "ai_bootstrap_status": "not_initialized",
                "ai_bootstrap_reason": None,
                "ai_fallback_active": False,
            },
        )

        with patch("app.main.importlib.import_module", return_value=fake_legacy_api):
            payload = app_main._build_operator_health_payload()

        self.assertEqual(bootstrap_calls, [("canonical_health", False)])
        self.assertEqual(payload["ai_status"], "not_initialized")

    def test_bootstrap_prefer_real_from_env(self):
        with patch.dict("os.environ", {"AAIS_MODEL_MODE": "real"}, clear=False):
            self.assertTrue(app_main._bootstrap_prefer_real())
        with patch.dict("os.environ", {"AAIS_BOOTSTRAP_REAL_AT_STARTUP": "1"}, clear=False):
            self.assertTrue(app_main._bootstrap_prefer_real())
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(app_main._bootstrap_prefer_real())

    def test_health_details_skips_bootstrap_when_initialized(self):
        bootstrap_calls: list[str] = []

        fake_legacy_api = types.SimpleNamespace(
            bootstrap_ai_runtime=lambda reason="startup": bootstrap_calls.append(reason),
            _build_ai_runtime_status=lambda: {
                "requested_model_mode": "real",
                "active_model_mode": "real",
                "ai_status": "initialized",
                "ai_bootstrap_status": "initialized",
                "ai_bootstrap_reason": "run_api",
                "ai_fallback_active": False,
            },
            system_guard=types.SimpleNamespace(snapshot=lambda limit_events=4: {"status": "nominal"}),
            dreamspace=types.SimpleNamespace(snapshot=lambda limit_dreams=2: {"status": "stopped"}),
        )

        with patch("app.main.importlib.import_module", return_value=fake_legacy_api):
            with TestClient(app_main.app) as client:
                response = client.get("/health/details")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(bootstrap_calls, [])
        self.assertEqual(response.json().get("ai_status"), "initialized")

    def test_contractor_health_rows_skip_probes_in_mock_mode(self):
        with patch.dict("os.environ", {"AAIS_MODEL_MODE": "mock"}, clear=False):
            rows = app_main._contractor_health_rows()
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row.get("skipped"), "mock_mode")
            self.assertNotIn("status", row)

    def test_build_operator_health_payload_degrades_cleanly_when_legacy_runtime_is_unavailable(self):
        with patch("app.main.importlib.import_module", side_effect=RuntimeError("legacy bridge unavailable")):
            payload = app_main._build_operator_health_payload()

        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["service"], "AAIS Workflow Shell")
        self.assertEqual(payload["ai_status"], "not_initialized")
        self.assertIn("legacy bridge unavailable", payload["ai_init_error"])

    def test_compact_health_endpoint_exposes_ai_status(self):
        fake_legacy_api = types.SimpleNamespace(
            bootstrap_ai_runtime=lambda reason="startup": None,
            _build_ai_runtime_status=lambda: {
                "requested_model_mode": "real",
                "active_model_mode": "real",
                "ai_status": "initialized",
                "ai_bootstrap_status": "initialized",
                "ai_bootstrap_reason": "run_api",
                "ai_fallback_active": False,
            },
            system_guard=types.SimpleNamespace(snapshot=lambda limit_events=4: {"status": "nominal"}),
            dreamspace=types.SimpleNamespace(snapshot=lambda limit_dreams=2: {"status": "stopped"}),
        )

        with patch("app.main.importlib.import_module", return_value=fake_legacy_api):
            with TestClient(app_main.app) as client:
                response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get("ai_status"), "initialized")
        self.assertEqual(body.get("ai_bootstrap_status"), "initialized")


if __name__ == "__main__":
    unittest.main()
