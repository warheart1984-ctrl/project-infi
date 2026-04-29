"""Tests for the bounded governed event chain."""

from pathlib import Path
import shutil
import tempfile
import unittest

from src.governed_event_chain import governed_event, validate_governed_event_result
from src.immune_system import ImmuneSystemController
from src.phase_gate import reset_registry


class TestGovernedEventChain(unittest.TestCase):
    """Verify predictor, invariant, and immune coordination stays bounded."""

    def setUp(self):
        reset_registry()
        self.temp_root = Path(tempfile.mkdtemp(prefix="governed-event-chain-"))
        self.immune = ImmuneSystemController(runtime_dir=self.temp_root)

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_governed_event_allows_consistent_prediction(self):
        event = {
            "source_pipeline_id": "gdp_test",
            "runtime_context": "live_runtime",
            "active_lane": "direct_cognitive",
            "traffic_class": "core_cognition",
            "surface_node": "jar",
            "immune_response": "ALLOW",
            "signal_count": 5,
            "signals": [
                {
                    "signal_type": "runtime_boundary",
                    "signal_class": "live_runtime_active",
                    "stable_key": "runtime_boundary:live_runtime",
                    "severity": "low",
                    "status": "observed",
                    "data_sufficiency": "sufficient",
                    "attributes": {"runtime_context": "live_runtime"},
                },
                {
                    "signal_type": "lane_activity",
                    "signal_class": "direct_lane_active",
                    "stable_key": "lane_activity:direct_cognitive",
                    "severity": "low",
                    "status": "observed",
                    "data_sufficiency": "sufficient",
                    "attributes": {"active_lane": "direct_cognitive"},
                },
                {
                    "signal_type": "system_posture",
                    "signal_class": "stable_posture",
                    "stable_key": "system_posture:stable:low",
                    "severity": "low",
                    "status": "observed",
                    "data_sufficiency": "sufficient",
                    "attributes": {"system_mode": "stable", "risk_level": "low"},
                },
                {
                    "signal_type": "packet_activity",
                    "signal_class": "packet_flow_observed",
                    "stable_key": "packet_activity:3:0:2",
                    "severity": "low",
                    "status": "observed",
                    "data_sufficiency": "sufficient",
                    "attributes": {
                        "forward_packet_count": 3,
                        "service_packet_count": 0,
                        "return_packet_count": 2,
                        "total_packet_count": 5,
                        "forward_intents": ["result", "route", "express"],
                        "service_intents": [],
                        "return_intents": ["ack"],
                    },
                },
                {
                    "signal_type": "turn_delta",
                    "signal_class": "turn_state_stable",
                    "stable_key": "turn_delta:stable",
                    "severity": "low",
                    "status": "delta",
                    "data_sufficiency": "sufficient",
                    "attributes": {
                        "has_previous_turn": True,
                        "runtime_context_changed": False,
                        "lane_changed": False,
                        "traffic_class_changed": False,
                        "response_mode_changed": False,
                        "contract_changed": False,
                        "tool_changed": False,
                        "immune_response_changed": False,
                        "system_mode_changed": False,
                        "risk_level_changed": False,
                        "surface_node_changed": False,
                        "change_count": 0,
                        "stable_repeat": True,
                    },
                },
            ],
            "packet_metrics": {
                "forward_packet_count": 3,
                "service_packet_count": 0,
                "return_packet_count": 2,
                "total_packet_count": 5,
                "forward_intents": ["result", "route", "express"],
                "service_intents": [],
                "return_intents": ["ack"],
            },
            "delta": {
                "has_previous_turn": True,
                "runtime_context_changed": False,
                "lane_changed": False,
                "traffic_class_changed": False,
                "response_mode_changed": False,
                "contract_changed": False,
                "tool_changed": False,
                "immune_response_changed": False,
                "system_mode_changed": False,
                "risk_level_changed": False,
                "surface_node_changed": False,
                "change_count": 0,
                "stable_repeat": True,
            },
            "validation": {
                "runtime_context_explicit": True,
                "signal_shape_uniform": True,
                "signal_count_bounded": True,
                "signal_count_matches": True,
                "stable_keys_unique": True,
                "turn_delta_present": True,
                "delta_shape_complete": True,
                "packet_metrics_complete": True,
            },
            "system_state": {"user_mode": "think", "system_mode": "stable", "risk_level": "low"},
        }

        result = governed_event(
            event,
            runtime_context="live_runtime",
            immune_controller=self.immune,
        )

        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["status"], "proceed")
        self.assertIsNone(result["immune_action"])
        self.assertTrue(result["invariant_result"]["allows"])
        self.assertTrue(all(validate_governed_event_result(result).values()))

    def test_governed_event_blocks_invalid_prediction_and_triggers_immune(self):
        event = {
            "runtime_context": "live_runtime",
            "immune_response": "ALLOW",
            "signal_count": 2,
            "signals": [{}, {}],
            "validation": {
                "runtime_context_explicit": True,
                "signal_shape_uniform": True,
                "signal_count_bounded": True,
                "signal_count_matches": True,
                "stable_keys_unique": True,
                "turn_delta_present": True,
                "delta_shape_complete": True,
                "packet_metrics_complete": True,
            },
        }
        prediction = {
            "module_id": "aais.realtime_event_cause_predictor",
            "version": "0.1",
            "status": "bounded_inference",
            "cause_class": "conflicting_signal_state",
            "confidence": 0.74,
            "supporting_signals": ["turn_shift_detected"],
            "conflict_flags": ["tool_lane_and_stable_repeat"],
            "data_sufficiency": "sufficient",
            "recommended_state": "proceed",
            "runtime_context": "live_runtime",
            "source_pipeline_id": "gdp_test",
            "signal_count": 2,
            "phase_gate": {"decision": "ALLOW"},
            "advisory_only": True,
        }

        result = governed_event(
            event,
            prediction=prediction,
            runtime_context="live_runtime",
            immune_controller=self.immune,
        )

        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["invariant_result"]["allows"])
        self.assertIn("conflict_safe_state", result["invariant_result"]["failed_invariants"])
        self.assertIsInstance(result["immune_action"], dict)
        self.assertEqual(result["immune_action"]["event"]["action"], "observe_protocol_signal")
        self.assertTrue(all(validate_governed_event_result(result).values()))


if __name__ == "__main__":
    unittest.main()
