"""Tests for the reusable verification gate policy."""

import unittest

from src.verification_gate import (
    GateDecision,
    VerificationTestResult,
    evaluate_verification_gate,
    normalize_verification_results,
)


class TestVerificationGate(unittest.TestCase):
    """Ensure the verification gate stays deterministic and auditable."""

    def test_gate_marks_clean_results_as_eligible(self):
        results = normalize_verification_results(
            [
                {
                    "test_id": "verification_1",
                    "law": 2,
                    "intent": 3,
                    "role": 2,
                    "constraint": 2,
                    "drift": 1,
                    "tags": [],
                }
            ]
        )

        evaluation = evaluate_verification_gate(results)

        self.assertEqual(evaluation.decision, GateDecision.ELIGIBLE)
        self.assertEqual(evaluation.reasons, [])
        self.assertEqual(evaluation.failed_tests, [])

    def test_gate_blocks_on_law_break_and_repeat_drift_instability(self):
        results = [
            VerificationTestResult(
                test_id="verification_1",
                law=1,
                intent=2,
                role=2,
                constraint=2,
                drift=2,
                tags={"LAW_BREAK"},
            ),
            VerificationTestResult(
                test_id="verification_2",
                law=2,
                intent=1,
                role=2,
                constraint=2,
                drift=1,
                tags={"ROLE_DRIFT", "DRIFT_INSTABILITY"},
                is_repeat_test=True,
            ),
            VerificationTestResult(
                test_id="verification_3",
                law=2,
                intent=2,
                role=2,
                constraint=2,
                drift=1,
                tags={"ROLE_DRIFT"},
            ),
        ]

        evaluation = evaluate_verification_gate(results)

        self.assertEqual(evaluation.decision, GateDecision.BLOCK)
        self.assertIn("verification_1: LAW_BREAK present", evaluation.reasons)
        self.assertIn("verification_1: Law < 2", evaluation.reasons)
        self.assertIn("verification_2: Intent < 2", evaluation.reasons)
        self.assertIn("verification_2: DRIFT_INSTABILITY in repeat test", evaluation.reasons)
        self.assertIn("ROLE_DRIFT occurred more than once", evaluation.reasons)
        self.assertEqual(evaluation.failed_tests, ["verification_1", "verification_2"])
