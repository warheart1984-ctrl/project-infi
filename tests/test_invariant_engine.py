"""Tests for the invariant engine module."""

import unittest

from src.invariant_engine import InvariantEngine, MathInvariants


class TestInvariantEngine(unittest.TestCase):
    """Verify the invariant engine stays deterministic across supported domains."""

    def test_matrix_invariants_returns_expected_values(self):
        result = MathInvariants.matrix_invariants([[1, 2], [3, 4]])

        self.assertEqual(result["trace"], 5.0)
        self.assertAlmostEqual(result["determinant"], -2.0, places=6)
        self.assertEqual(result["rank"], 2)
        self.assertAlmostEqual(result["frobenius_norm"], 30 ** 0.5, places=6)
        self.assertEqual(len(result["eigenvalues"]), 2)

    def test_polynomial_invariants_returns_expected_values(self):
        result = MathInvariants.polynomial_invariants([1, -5, 6])

        self.assertEqual(result["degree"], 2)
        self.assertAlmostEqual(result["discriminant"], 1.0, places=6)
        self.assertAlmostEqual(result["leading_coefficient"], 1.0, places=6)

    def test_topological_invariants_returns_expected_values(self):
        result = MathInvariants.topological_invariants([(1, 2), (2, 3), (3, 1), (4, 5)])

        self.assertEqual(result["vertices"], 5)
        self.assertEqual(result["edges"], 4)
        self.assertEqual(result["connected_components"], 2)
        self.assertEqual(result["euler_characteristic"], 3)
        self.assertEqual(result["number_of_cycles"], 1)

    def test_statistical_invariants_returns_expected_values(self):
        result = MathInvariants.statistical_invariants([2, 4, 4, 4, 5, 5, 7, 9])

        self.assertAlmostEqual(result["mean"], 5.0, places=6)
        self.assertAlmostEqual(result["variance"], 4.0, places=6)
        self.assertAlmostEqual(result["standard_deviation"], 2.0, places=6)
        self.assertTrue(isinstance(result["skewness"], float))
        self.assertTrue(isinstance(result["kurtosis"], float))

    def test_cross_domain_report_collects_multiple_domains(self):
        result = InvariantEngine.cross_domain_report(
            matrix=[[1, 0], [0, 1]],
            polynomial_coeffs=[1, 0, -1],
            edges=[("a", "b")],
            data=[1, 2, 3],
        )

        self.assertEqual(result["module"], "invariant_engine")
        self.assertEqual(result["domain_count"], 4)
        self.assertEqual(result["available_domains"], ["matrix", "polynomial", "topology", "statistics"])
        self.assertIn("matrix", result["domains"])
        self.assertIn("statistics", result["domains"])

    def test_cross_domain_report_requires_at_least_one_input(self):
        with self.assertRaises(ValueError):
            InvariantEngine.cross_domain_report()

    def test_runtime_event_prediction_allows_consistent_bounded_state(self):
        event = {
            "runtime_context": "live_runtime",
            "signal_count": 2,
            "signals": [{}, {}],
            "immune_response": "ALLOW",
            "validation": {
                "runtime_context_explicit": True,
                "signal_shape_uniform": True,
            },
        }
        prediction = {
            "status": "bounded_inference",
            "cause_class": "steady_state",
            "confidence": 0.82,
            "supporting_signals": ["turn_state_stable"],
            "conflict_flags": [],
            "data_sufficiency": "sufficient",
            "recommended_state": "observe",
            "runtime_context": "live_runtime",
            "signal_count": 2,
            "phase_gate": {"decision": "ALLOW"},
            "advisory_only": True,
        }

        result = InvariantEngine.validate_realtime_event_prediction(event, prediction)

        self.assertTrue(result["allows"])
        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["failed_invariants"])

    def test_runtime_event_prediction_blocks_conflicting_proceed_state(self):
        event = {
            "runtime_context": "live_runtime",
            "signal_count": 1,
            "signals": [{}],
            "immune_response": "ALLOW",
            "validation": {"runtime_context_explicit": True},
        }
        prediction = {
            "status": "bounded_inference",
            "cause_class": "conflicting_signal_state",
            "confidence": 0.61,
            "supporting_signals": ["turn_shift_detected"],
            "conflict_flags": ["lane_and_tool_tension"],
            "data_sufficiency": "sufficient",
            "recommended_state": "proceed",
            "runtime_context": "live_runtime",
            "signal_count": 1,
            "phase_gate": {"decision": "ALLOW"},
            "advisory_only": True,
        }

        result = InvariantEngine.validate_realtime_event_prediction(event, prediction)

        self.assertFalse(result["allows"])
        self.assertEqual(result["status"], "fail")
        self.assertIn("conflict_safe_state", result["failed_invariants"])

    def test_validate_bridge_packet_accepts_governed_deliberation(self):
        normalized = {
            "source": "ugr_runtime",
            "type": "deliberation_request",
            "payload": {
                "question": "Why is latency high?",
                "execution_intent": "observe",
                "runtime_context": "live_runtime",
                "bridge_attestation": {"signature": "test"},
            },
            "effectful": False,
        }
        governance = {
            "packet_type": "deliberation_request",
            "runtime_context": "live_runtime",
            "execution_intent": "observe",
            "effectful": False,
            "source": "ugr_runtime",
        }
        result = InvariantEngine.validate_bridge_packet(normalized, governance)
        self.assertTrue(result["allows"])
        self.assertEqual(result["module_id"], "aais.invariant_engine.bridge_guard")

    def test_validate_bridge_packet_blocks_missing_attestation(self):
        normalized = {
            "source": "ugr_runtime",
            "type": "deliberation_request",
            "payload": {
                "question": "Why is latency high?",
                "execution_intent": "observe",
                "runtime_context": "live_runtime",
            },
            "effectful": False,
        }
        governance = {
            "packet_type": "deliberation_request",
            "runtime_context": "live_runtime",
            "execution_intent": "observe",
            "effectful": False,
            "source": "ugr_runtime",
        }
        result = InvariantEngine.validate_bridge_packet(normalized, governance)
        self.assertFalse(result["allows"])
        self.assertIn("bridge_attestation_present", result["failed_invariants"])


if __name__ == "__main__":
    unittest.main()
