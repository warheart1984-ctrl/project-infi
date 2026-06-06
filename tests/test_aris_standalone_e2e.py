"""ARIS standalone service E2E (skipped when sidecar is not running)."""

from __future__ import annotations

import os
import unittest

import pytest


@pytest.mark.skipif(
    os.getenv("ARIS_STANDALONE_E2E", "").strip().lower() not in {"1", "true", "yes"},
    reason="Set ARIS_STANDALONE_E2E=1 with aris_service running",
)
def test_aris_standalone_health_and_admit():
    from src.aris_service_client import build_aris_client_status, evaluate_aris_admission

    os.environ["ARIS_MODE"] = "standalone"
    status = build_aris_client_status()
    assert status.get("mode") == "standalone"
    result = evaluate_aris_admission(details={"pattern_share_mode": "local_only"})
    assert result.get("runtime_profile")


class ArisStandaloneSkippedTests(unittest.TestCase):
    def test_embedded_mode_default(self):
        from src.aris_service_client import build_aris_client_status

        os.environ.pop("ARIS_MODE", None)
        status = build_aris_client_status()
        self.assertEqual(status.get("mode"), "embedded")
