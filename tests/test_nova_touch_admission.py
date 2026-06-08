"""Tests for Nova touch admission."""

from __future__ import annotations

import unittest

from src.nova_touch_admission import admit_touch_event, build_nova_touch_admission_status


class NovaTouchAdmissionTests(unittest.TestCase):
    def test_admit_tap_maps_to_keystroke(self):
        result = admit_touch_event(
            {
                "touch_kind": "tap",
                "session_id": "nova-session-1",
                "target": "companion_surface",
            }
        )
        self.assertTrue(result["admitted"])
        self.assertFalse(result["logs_biometric_traces"])
        self.assertIn("keystroke_equivalent", result)

    def test_reject_invalid_kind(self):
        result = admit_touch_event({"touch_kind": "biometric_scan", "session_id": "s1"})
        self.assertFalse(result["admitted"])

    def test_status_live(self):
        status = build_nova_touch_admission_status()
        self.assertTrue(status["live"])
        self.assertFalse(status["persistent_storage"])
