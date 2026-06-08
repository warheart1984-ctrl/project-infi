"""Tests for Twilio operator pager integration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.operator_pager import (
    format_dashboard_alert_page,
    format_immune_escalation_page,
    maybe_page_dashboard_alerts,
    maybe_page_immune_escalation,
    pager_is_configured,
    send_operator_page,
    should_page_for_dashboard_alert,
    should_page_for_escalation,
)

class OperatorPagerTests(unittest.TestCase):
    def test_should_page_for_material_escalations(self):
        self.assertTrue(should_page_for_escalation({"response": "CLAMP", "allowed": True}))
        self.assertTrue(should_page_for_escalation({"response": "REROUTE", "allowed": True}))
        self.assertTrue(should_page_for_escalation({"response": "REJECT", "allowed": False}))
        self.assertFalse(should_page_for_escalation({"response": "ALLOW", "allowed": False}))

    def test_format_message_includes_session_and_charter_hint(self):
        body = format_immune_escalation_page(
            "sess-42",
            {"response": "CLAMP", "allowed": True, "reason": "predictor_threshold"},
        )
        self.assertIn("sess-42", body)
        self.assertIn("CLAMP", body)
        self.assertIn("co-collaboration charter", body)

    def test_send_skips_when_not_configured(self):
        result = send_operator_page("test", config={})
        self.assertFalse(result["ok"])
        self.assertTrue(result["skipped"])

    def test_pager_is_configured_with_from_number(self):
        cfg = {
            "account_sid": "AC123",
            "auth_token": "secret",
            "from_number": "+15551234567",
            "messaging_service_sid": "",
            "operator_to": "+15557654321",
        }
        self.assertTrue(pager_is_configured(cfg))

    @patch("src.operator_pager.send_operator_page")
    def test_maybe_page_invoked_for_clamp(self, mock_send):
        mock_send.return_value = {"ok": True, "skipped": False, "sid": "SM123"}
        escalation = {"response": "CLAMP", "allowed": True}
        result = maybe_page_immune_escalation("sess-1", escalation)
        mock_send.assert_called_once()
        self.assertTrue(result["ok"])

    @patch("src.operator_pager.send_operator_page")
    def test_maybe_page_skips_allow(self, mock_send):
        escalation = {"response": "ALLOW", "allowed": False, "reason": "below_threshold"}
        result = maybe_page_immune_escalation("sess-1", escalation)
        mock_send.assert_not_called()
        self.assertIsNone(result)

    def test_should_page_for_high_dashboard_alerts(self):
        self.assertTrue(should_page_for_dashboard_alert({"id": "mesh-degraded", "severity": "high"}))
        self.assertFalse(should_page_for_dashboard_alert({"id": "rail-express-high", "severity": "medium"}))

    def test_format_dashboard_alert_page(self):
        body = format_dashboard_alert_page(
            {"id": "mesh-degraded", "severity": "high", "summary": "mesh unhealthy services=2"}
        )
        self.assertIn("mesh-degraded", body)
        self.assertIn("HIGH", body)

    @patch("src.operator_pager.send_operator_page")
    def test_dashboard_alert_dedupes_by_fingerprint(self, mock_send):
        mock_send.return_value = {"ok": True, "skipped": False, "sid": "SM999"}
        alert = {"id": "mesh-degraded", "severity": "high", "summary": "mesh unhealthy services=2"}
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "pager_state.json"
            with patch.dict("os.environ", {"OPERATOR_PAGER_STATE_PATH": str(state_path)}):
                first = maybe_page_dashboard_alerts([alert])
                second = maybe_page_dashboard_alerts([alert])
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        mock_send.assert_called_once()
