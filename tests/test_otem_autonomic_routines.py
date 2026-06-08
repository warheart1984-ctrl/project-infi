"""Tests for OTEM autonomic routines."""

from __future__ import annotations

import os
import unittest

from src.otem_autonomic_routines import (
    arc_allowed,
    execute_autonomic_routine,
    routine_by_id,
)


class OtemAutonomicRoutinesTests(unittest.TestCase):
    def test_routine_registry(self):
        routine = routine_by_id("health_poll")
        self.assertIsNotNone(routine)
        self.assertEqual(routine["arc_class"], "ARC-0")

    def test_blocked_when_disabled(self):
        prior = os.environ.get("AAIS_OTEM_AUTONOMIC_ENABLED")
        os.environ["AAIS_OTEM_AUTONOMIC_ENABLED"] = "0"
        try:
            result = execute_autonomic_routine("health_poll")
            self.assertEqual(result["outcome"], "blocked")
        finally:
            if prior is None:
                os.environ.pop("AAIS_OTEM_AUTONOMIC_ENABLED", None)
            else:
                os.environ["AAIS_OTEM_AUTONOMIC_ENABLED"] = prior

    def test_arc0_runs_when_enabled(self):
        prior = os.environ.get("AAIS_OTEM_AUTONOMIC_ENABLED")
        os.environ["AAIS_OTEM_AUTONOMIC_ENABLED"] = "1"
        try:
            result = execute_autonomic_routine("health_poll", session_id="test-session")
            self.assertEqual(result["outcome"], "completed")
            self.assertIn("result", result)
        finally:
            if prior is None:
                os.environ.pop("AAIS_OTEM_AUTONOMIC_ENABLED", None)
            else:
                os.environ["AAIS_OTEM_AUTONOMIC_ENABLED"] = prior

    def test_arc_ceiling(self):
        self.assertTrue(arc_allowed("ARC-0"))
        self.assertTrue(arc_allowed("ARC-1"))
