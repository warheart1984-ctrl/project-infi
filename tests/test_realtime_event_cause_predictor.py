"""Tests for the realtime event-and-cause prediction module."""

from datetime import datetime
from src.datetime_compat import UTC
import unittest

from src.governed_direct_pipeline import OPERATION_CODES, build_pipeline_packet
from src.phase_gate import reset_registry
from src.realtime_event_cause_predictor import (
    EVENT_CODES,
    REALTIME_CHANNEL,
    RealtimeEventCausePredictor,
    assert_valid_interpreted_event_state,
    assert_valid_prediction_trace,
)


class TestRealtimeEventCausePredictor(unittest.TestCase):
    """Verify the governed realtime predictor stays compact and deterministic."""

    def setUp(self):
        reset_registry()

    def test_packet_contract_supports_prediction_ops_on_rt_channel(self):
        """Prediction packets should expose the new op codes and compact rt payload keys."""
        packet = build_pipeline_packet(
            source="pred",
            target="gb",
            lane="direct_cognitive",
            compact_channel=REALTIME_CHANNEL,
            priority="high",
            intent="predict_event",
            state={"user_mode": "normal", "system_mode": "stable", "risk_level": "low"},
            payload={
                "ev": 7,
                "ca": [8, 10],
                "conf": 87,
                "horiz": 180,
                "meaning": "prediction_event",
                "constraints": ["no_tools", "bounded_reply"],
                "tone": "neutral",
            },
            compact_payload={"ev": 7, "ca": [8, 10], "conf": 87, "horiz": 180},
            route=["pred", "gb"],
            ref="ctx77",
        )

        self.assertEqual(OPERATION_CODES["predict_event"], 22)
        self.assertEqual(OPERATION_CODES["predict_cause"], 23)
        self.assertEqual(packet["compact"]["op"], 22)
        self.assertEqual(packet["compact"]["ch"], REALTIME_CHANNEL)
        self.assertEqual(packet["compact"]["pl"]["ev"], 7)
        self.assertEqual(packet["compact"]["pl"]["ca"], [8, 10])
        self.assertEqual(packet["compact"]["pl"]["conf"], 87)
        self.assertEqual(packet["compact"]["pl"]["horiz"], 180)

    def test_context_switch_predicts_session_transition_trace(self):
        """Context switches should emit advisory session-transition predictions."""
        predictor = RealtimeEventCausePredictor()
        predictor.predict(
            {
                "context_ref": "ctx10",
                "keyboard_rhythm": 0.32,
                "bpm": 84,
                "temp": 35.2,
                "user_mode": "normal",
                "system_mode": "stable",
                "observed_at": datetime(2026, 4, 18, 13, 30, tzinfo=UTC),
            }
        )

        trace = predictor.build_trace(
            {
                "context_ref": "ctx11",
                "keyboard_rhythm": 0.74,
                "bpm": 93,
                "temp": 35.7,
                "user_mode": "planning",
                "system_mode": "stable",
                "observed_at": datetime(2026, 4, 18, 13, 30, 1, tzinfo=UTC),
            }
        )

        prediction = trace["prediction"]
        self.assertEqual(prediction["event_code"], EVENT_CODES["session_transition"])
        self.assertIn(8, prediction["cause_codes"])
        self.assertIn(10, prediction["cause_codes"])
        self.assertEqual(trace["channel"], REALTIME_CHANNEL)
        self.assertEqual(len(trace["forward_packets"]), 4)
        self.assertEqual(len(trace["return_packets"]), 3)
        self.assertTrue(trace["validation"]["rt_channel_only"])
        self.assertTrue(trace["validation"]["packet_size_under_limit"])
        assert_valid_prediction_trace(trace)

    def test_degraded_system_predicts_system_transition(self):
        """System strain should dominate the event forecast and stay governed."""
        predictor = RealtimeEventCausePredictor()
        predictor.predict(
            {
                "context_ref": "ctx20",
                "keyboard_rhythm": 0.46,
                "bpm": 88,
                "temp": 34.8,
                "user_mode": "normal",
                "system_mode": "stable",
                "observed_at": datetime(2026, 4, 18, 14, 0, tzinfo=UTC),
            }
        )

        trace = predictor.build_trace(
            {
                "context_ref": "ctx20",
                "keyboard_rhythm": 0.52,
                "bpm": 89,
                "temp": 36.3,
                "user_mode": "normal",
                "system_mode": "degraded",
                "observed_at": datetime(2026, 4, 18, 14, 0, 1, tzinfo=UTC),
            }
        )

        prediction = trace["prediction"]
        self.assertEqual(prediction["event_code"], EVENT_CODES["system_transition"])
        self.assertIn(7, prediction["cause_codes"])
        self.assertIn(9, prediction["cause_codes"])
        self.assertGreaterEqual(prediction["confidence"], 70)
        self.assertTrue(trace["validation"]["god_brain_in_path"])
        self.assertTrue(trace["validation"]["jarvis_authority_preserved"])
        self.assertTrue(trace["validation"]["no_service_tool_intents"])

    def test_signal_feed_classifies_operator_service_request(self):
        """Operator-runtime service activity should classify as an operator service request."""
        predictor = RealtimeEventCausePredictor()

        interpreted = predictor.interpret_signal_feed(
            {
                "source_pipeline_id": "gdp_test",
                "runtime_context": "operator_runtime",
                "active_lane": "service_tools",
                "traffic_class": "service",
                "surface_node": "jar",
                "immune_response": "ALLOW",
                "signal_count": 6,
                "signals": [
                    {
                        "signal_type": "runtime_boundary",
                        "signal_class": "operator_runtime_active",
                        "stable_key": "runtime_boundary:operator_runtime",
                        "severity": "medium",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {"runtime_context": "operator_runtime"},
                    },
                    {
                        "signal_type": "lane_activity",
                        "signal_class": "service_lane_active",
                        "stable_key": "lane_activity:service_tools",
                        "severity": "medium",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {"active_lane": "service_tools"},
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
                        "stable_key": "packet_activity:1:2:1",
                        "severity": "medium",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {
                            "forward_packet_count": 1,
                            "service_packet_count": 2,
                            "return_packet_count": 1,
                            "total_packet_count": 4,
                            "forward_intents": ["route"],
                            "service_intents": ["tool_call", "tool_result"],
                            "return_intents": ["ack"],
                        },
                    },
                    {
                        "signal_type": "turn_delta",
                        "signal_class": "turn_shift_detected",
                        "stable_key": "turn_delta:shift",
                        "severity": "medium",
                        "status": "delta",
                        "data_sufficiency": "sufficient",
                        "attributes": {
                            "has_previous_turn": True,
                            "runtime_context_changed": False,
                            "lane_changed": True,
                            "traffic_class_changed": True,
                            "response_mode_changed": True,
                            "contract_changed": True,
                            "tool_changed": True,
                            "immune_response_changed": False,
                            "system_mode_changed": False,
                            "risk_level_changed": False,
                            "surface_node_changed": False,
                            "change_count": 4,
                            "stable_repeat": False,
                        },
                    },
                    {
                        "signal_type": "tool_activity",
                        "signal_class": "service_tool_completed",
                        "stable_key": "tool_activity:mystic_reading:completed",
                        "severity": "medium",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {
                            "tool_type": "mystic_reading",
                            "tool_status": "completed",
                            "capability_module": "mystic",
                        },
                    },
                ],
                "packet_metrics": {
                    "forward_packet_count": 1,
                    "service_packet_count": 2,
                    "return_packet_count": 1,
                    "total_packet_count": 4,
                    "forward_intents": ["route"],
                    "service_intents": ["tool_call", "tool_result"],
                    "return_intents": ["ack"],
                },
                "delta": {
                    "has_previous_turn": True,
                    "runtime_context_changed": False,
                    "lane_changed": True,
                    "traffic_class_changed": True,
                    "response_mode_changed": True,
                    "contract_changed": True,
                    "tool_changed": True,
                    "immune_response_changed": False,
                    "system_mode_changed": False,
                    "risk_level_changed": False,
                    "surface_node_changed": False,
                    "change_count": 4,
                    "stable_repeat": False,
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
                "system_state": {"user_mode": "operator", "system_mode": "stable", "risk_level": "low"},
            }
        )

        self.assertEqual(interpreted["cause_class"], "operator_service_request")
        self.assertEqual(interpreted["recommended_state"], "proceed")
        self.assertGreaterEqual(interpreted["confidence"], 0.9)
        self.assertEqual(interpreted["data_sufficiency"], "sufficient")
        self.assertEqual(interpreted["phase_gate"]["decision"], "ALLOW")
        assert_valid_interpreted_event_state(interpreted)

    def test_signal_feed_low_confidence_pauses_on_insufficient_data(self):
        """Insufficient feeds should fail safely without inventing a cause."""
        predictor = RealtimeEventCausePredictor()

        interpreted = predictor.interpret_signal_feed(
            {
                "runtime_context": "live_runtime",
                "signals": [],
                "packet_metrics": {},
                "delta": {},
                "validation": {},
            }
        )

        self.assertEqual(interpreted["status"], "insufficient_data")
        self.assertEqual(interpreted["cause_class"], "insufficient_signal")
        self.assertLess(interpreted["confidence"], 0.2)
        self.assertEqual(interpreted["recommended_state"], "pause")
        assert_valid_interpreted_event_state(interpreted)

    def test_signal_feed_conflicts_degrade_safely(self):
        """Conflicting bounded signals should not be converted into an aggressive interpretation."""
        predictor = RealtimeEventCausePredictor()

        interpreted = predictor.interpret_signal_feed(
            {
                "runtime_context": "live_runtime",
                "active_lane": "direct_cognitive",
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
                        "stable_key": "packet_activity:1:0:1",
                        "severity": "low",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {
                            "forward_packet_count": 1,
                            "service_packet_count": 0,
                            "return_packet_count": 1,
                            "total_packet_count": 2,
                            "forward_intents": ["result"],
                            "service_intents": [],
                            "return_intents": ["ack"],
                        },
                    },
                    {
                        "signal_type": "tool_activity",
                        "signal_class": "service_tool_completed",
                        "stable_key": "tool_activity:v9_core:completed",
                        "severity": "medium",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {"tool_type": "v9_core", "tool_status": "completed"},
                    },
                ],
                "packet_metrics": {
                    "forward_packet_count": 1,
                    "service_packet_count": 0,
                    "return_packet_count": 1,
                    "total_packet_count": 2,
                    "forward_intents": ["result"],
                    "service_intents": [],
                    "return_intents": ["ack"],
                },
                "delta": {
                    "has_previous_turn": False,
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
                    "stable_repeat": False,
                },
                "validation": {
                    "runtime_context_explicit": True,
                    "signal_shape_uniform": True,
                    "signal_count_bounded": True,
                    "signal_count_matches": True,
                    "stable_keys_unique": True,
                    "turn_delta_present": False,
                    "delta_shape_complete": True,
                    "packet_metrics_complete": True,
                },
                "system_state": {"user_mode": "think", "system_mode": "stable", "risk_level": "low"},
            }
        )

        self.assertEqual(interpreted["cause_class"], "conflicting_signal_state")
        self.assertEqual(interpreted["recommended_state"], "degrade_safe")
        self.assertIn("direct_lane_with_tool_activity", interpreted["conflict_flags"])
        assert_valid_interpreted_event_state(interpreted)

    def test_signal_feed_repeatability_stays_stable_for_identical_input(self):
        """The bounded interpreter should return the same result for the same feed."""
        predictor = RealtimeEventCausePredictor()
        feed = {
            "source_pipeline_id": "gdp_same",
            "runtime_context": "live_runtime",
            "active_lane": "direct_cognitive",
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

        first = predictor.interpret_signal_feed(feed)
        second = predictor.interpret_signal_feed(feed)

        self.assertEqual(first["cause_class"], second["cause_class"])
        self.assertEqual(first["confidence"], second["confidence"])
        self.assertEqual(first["recommended_state"], second["recommended_state"])
        self.assertEqual(first["conflict_flags"], second["conflict_flags"])

    def test_signal_feed_unknown_state_handles_unsupported_signal_safely(self):
        """Unknown bounded signals should map to explicit unknown-safe handling."""
        predictor = RealtimeEventCausePredictor()

        interpreted = predictor.interpret_signal_feed(
            {
                "runtime_context": "live_runtime",
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
                        "signal_class": "mystery_lane",
                        "stable_key": "lane_activity:mystery_lane",
                        "severity": "low",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {"active_lane": "mystery_lane"},
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
                        "stable_key": "packet_activity:1:0:1",
                        "severity": "low",
                        "status": "observed",
                        "data_sufficiency": "sufficient",
                        "attributes": {
                            "forward_packet_count": 1,
                            "service_packet_count": 0,
                            "return_packet_count": 1,
                            "total_packet_count": 2,
                            "forward_intents": ["route"],
                            "service_intents": [],
                            "return_intents": ["ack"],
                        },
                    },
                    {
                        "signal_type": "turn_delta",
                        "signal_class": "mystery_delta",
                        "stable_key": "turn_delta:mystery_delta",
                        "severity": "medium",
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
                            "change_count": 1,
                            "stable_repeat": False,
                        },
                    },
                ],
                "packet_metrics": {
                    "forward_packet_count": 1,
                    "service_packet_count": 0,
                    "return_packet_count": 1,
                    "total_packet_count": 2,
                    "forward_intents": ["route"],
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
                    "change_count": 1,
                    "stable_repeat": False,
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
                "system_state": {"user_mode": "fast", "system_mode": "stable", "risk_level": "low"},
            }
        )

        self.assertEqual(interpreted["cause_class"], "unknown_state")
        self.assertEqual(interpreted["recommended_state"], "pause")
        self.assertLess(interpreted["confidence"], 0.4)
        assert_valid_interpreted_event_state(interpreted)


if __name__ == "__main__":
    unittest.main()
