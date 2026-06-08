"""Tests for immune policy enrollment."""

from __future__ import annotations

import unittest

from src.immune_policy_enrollment import evaluate_predictor_bounded_escalation


class ImmunePolicyEnrollmentTests(unittest.TestCase):
    def test_quarantine_blocked(self):
        result = evaluate_predictor_bounded_escalation(
            confidence=0.99,
            severity=0.99,
            requested_response="QUARANTINE",
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["response"], "REJECT")

    def test_clamp_allowed_at_threshold(self):
        result = evaluate_predictor_bounded_escalation(
            confidence=0.75,
            severity=0.1,
            requested_response="CLAMP",
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["response"], "CLAMP")

    def test_reroute_allowed_at_severity(self):
        result = evaluate_predictor_bounded_escalation(
            confidence=0.1,
            severity=0.85,
            requested_response="REROUTE",
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["response"], "REROUTE")
