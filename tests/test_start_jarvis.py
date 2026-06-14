"""Startup alignment tests for the Jarvis launcher."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.entrypoints import start_jarvis


class TestStartJarvis(unittest.TestCase):
    def test_build_frontend_env_pins_backend_url(self):
        env = start_jarvis.build_frontend_env(
            "http://127.0.0.1:5000",
            {"EXISTING": "1"},
        )

        self.assertEqual(env["EXISTING"], "1")
        self.assertEqual(env["VITE_API_URL"], "http://127.0.0.1:5000")
        self.assertEqual(env["REACT_APP_API_URL"], "http://127.0.0.1:5000")

    @patch("src.entrypoints.start_jarvis.http_ready")
    def test_resolve_existing_backend_prefers_canonical_runtime(self, mock_http_ready):
        mock_http_ready.side_effect = lambda url: url == start_jarvis.CANONICAL_BACKEND_HEALTH_URL

        result = start_jarvis.resolve_existing_backend()

        self.assertIsNotNone(result)
        self.assertEqual(result["backend_kind"], "canonical")
        self.assertEqual(result["backend_url"], start_jarvis.CANONICAL_BACKEND_URL)

    @patch("src.entrypoints.start_jarvis.http_ready")
    def test_resolve_existing_backend_falls_back_to_legacy_runtime(self, mock_http_ready):
        mock_http_ready.side_effect = lambda url: url == start_jarvis.LEGACY_BACKEND_HEALTH_URL

        result = start_jarvis.resolve_existing_backend()

        self.assertIsNotNone(result)
        self.assertEqual(result["backend_kind"], "legacy")
        self.assertEqual(result["backend_url"], start_jarvis.LEGACY_BACKEND_URL)

    @patch("src.entrypoints.start_jarvis.build_backend_candidates")
    @patch("src.entrypoints.start_jarvis.start_backend_candidate")
    @patch("src.entrypoints.start_jarvis.resolve_existing_backend")
    def test_ensure_backend_promotes_canonical_when_legacy_is_already_running(
        self,
        mock_resolve_existing_backend,
        mock_start_backend_candidate,
        mock_build_backend_candidates,
    ):
        legacy_backend = {
            "status": "existing",
            "backend_kind": "legacy",
            "backend_mode": "legacy",
            "backend_runtime": "already_running",
            "backend_url": start_jarvis.LEGACY_BACKEND_URL,
        }
        canonical_candidate = {
            "label": "local venv (canonical runtime)",
            "kind": "canonical",
            "mode": "canonical",
            "backend_url": start_jarvis.CANONICAL_BACKEND_URL,
        }
        canonical_backend = {
            "status": "started",
            "backend_kind": "canonical",
            "backend_mode": "canonical",
            "backend_runtime": "local venv (canonical runtime)",
            "backend_url": start_jarvis.CANONICAL_BACKEND_URL,
            "backend_pid": "1234",
        }
        mock_resolve_existing_backend.side_effect = [None, legacy_backend]
        mock_build_backend_candidates.return_value = [canonical_candidate]
        mock_start_backend_candidate.return_value = canonical_backend

        result = start_jarvis.ensure_backend()

        self.assertEqual(result, canonical_backend)
        mock_start_backend_candidate.assert_called_once_with(canonical_candidate)

    @patch("src.entrypoints.start_jarvis.build_backend_candidates")
    @patch("src.entrypoints.start_jarvis.start_backend_candidate")
    @patch("src.entrypoints.start_jarvis.resolve_existing_backend")
    def test_ensure_backend_keeps_legacy_when_canonical_promotion_fails(
        self,
        mock_resolve_existing_backend,
        mock_start_backend_candidate,
        mock_build_backend_candidates,
    ):
        legacy_backend = {
            "status": "existing",
            "backend_kind": "legacy",
            "backend_mode": "legacy",
            "backend_runtime": "already_running",
            "backend_url": start_jarvis.LEGACY_BACKEND_URL,
        }
        canonical_candidate = {
            "label": "local venv (canonical runtime)",
            "kind": "canonical",
            "mode": "canonical",
            "backend_url": start_jarvis.CANONICAL_BACKEND_URL,
        }
        mock_resolve_existing_backend.side_effect = [None, legacy_backend]
        mock_build_backend_candidates.return_value = [canonical_candidate]
        mock_start_backend_candidate.return_value = None

        result = start_jarvis.ensure_backend()

        self.assertEqual(result, legacy_backend)
        mock_start_backend_candidate.assert_called_once_with(canonical_candidate)


if __name__ == "__main__":
    unittest.main()
