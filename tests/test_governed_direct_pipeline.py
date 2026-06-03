"""Tests for the governed direct pipeline packet contract."""

import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.governed_direct_pipeline import (
    DIRECT_COGNITIVE_LANE,
    SERVICE_TOOL_LANE,
    _GOVERNED_PIPELINE_CACHE,
    build_governed_turn_pipeline,
    clear_governed_pipeline_cache,
    to_pipeline_envelope,
)
from src.jarvis_detachment_guard import jarvis_detachment_guard
from src.module_governance import module_governance
from src.phase_gate import reset_registry


class TestGovernedDirectPipeline(unittest.TestCase):
    """Verify core cognition and service/tool traffic stay on separate lanes."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="governed-pipeline-"))
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        self.original_detachment_guard_runtime_dir = jarvis_detachment_guard.runtime_dir
        module_governance.configure_runtime_dir(self.temp_root)
        module_governance.reset()
        jarvis_detachment_guard.configure_runtime_dir(self.temp_root)
        jarvis_detachment_guard.reset()
        reset_registry()

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        jarvis_detachment_guard.configure_runtime_dir(self.original_detachment_guard_runtime_dir)
        jarvis_detachment_guard.reset()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_core_turn_uses_direct_lane_with_uniform_packets(self):
        """Normal cognitive turns should stay on the governed direct lane."""
        pipeline = build_governed_turn_pipeline(
            response_mode="think",
            contract="gather_plan_answer",
            god_brain={
                "strategy_label": "Council Deliberation",
                "action_bias": "deliberate_then_answer",
                "surface_identity": "jarvis",
            },
            model_route={"id": "local_fast", "label": "Local Fast Route"},
        )

        self.assertEqual(pipeline["active_lane"], DIRECT_COGNITIVE_LANE)
        self.assertEqual(pipeline["traffic_class"], "core_cognition")
        self.assertFalse(pipeline["service_packets"])
        self.assertEqual(pipeline["direct_route"], ["llm", "gb", "jar"])
        self.assertTrue(pipeline["validation"]["uniform_packet_shape"])
        self.assertTrue(pipeline["validation"]["god_brain_in_path"])
        self.assertTrue(pipeline["validation"]["jarvis_authority_preserved"])
        self.assertTrue(pipeline["validation"]["direct_lane_tool_free"])
        self.assertEqual(pipeline["immune_protocol"]["response"], "ALLOW")
        self.assertTrue(pipeline["validation"]["immune_traffic_allowed"])

        first_packet = pipeline["forward_packets"][0]
        self.assertEqual(first_packet["source"], "llm")
        self.assertEqual(first_packet["target"], "gb")
        self.assertEqual(first_packet["lane"], DIRECT_COGNITIVE_LANE)
        self.assertIn("compact", first_packet)
        self.assertEqual(first_packet["compact"]["ch"], "core")
        realtime_feed = pipeline["realtime_signal_feed"]
        witness_input = pipeline["continuity_witness_input"]
        signal_types = [signal["signal_type"] for signal in realtime_feed["signals"]]
        predictor = pipeline["realtime_event_cause_predictor"]
        governed_event = pipeline["governed_event"]
        sentinel = pipeline["operator_health_sentinel"]
        self.assertEqual(realtime_feed["runtime_context"], "live_runtime")
        self.assertEqual(realtime_feed["active_lane"], DIRECT_COGNITIVE_LANE)
        self.assertEqual(realtime_feed["packet_metrics"]["service_packet_count"], 0)
        self.assertIn("runtime_boundary", signal_types)
        self.assertIn("turn_delta", signal_types)
        self.assertEqual(realtime_feed["signals"][-1]["signal_class"], "baseline_only")
        self.assertEqual(predictor["cause_class"], "steady_state")
        self.assertEqual(predictor["recommended_state"], "observe")
        self.assertEqual(sentinel["operator_state"], "stable")
        self.assertEqual(sentinel["recommended_mode"], "normal")
        self.assertTrue(sentinel["advisory_only"])
        self.assertEqual(witness_input["module_id"], "AAIS-CW-01")
        self.assertEqual(witness_input["subsystem"], "JARVIS")
        self.assertEqual(witness_input["fingerprint"]["lane_type"], DIRECT_COGNITIVE_LANE)
        self.assertEqual(predictor["phase_gate"]["decision"], "ALLOW")
        self.assertEqual(governed_event["decision"], "ALLOW")
        self.assertIsNone(governed_event["immune_action"])
        self.assertTrue(all(realtime_feed["validation"].values()))
        self.assertTrue(pipeline["validation"]["realtime_signal_feed_valid"])
        self.assertTrue(pipeline["validation"]["realtime_event_cause_predictor_valid"])
        self.assertTrue(pipeline["validation"]["governed_event_valid"])
        self.assertTrue(pipeline["validation"]["operator_health_sentinel_valid"])
        self.assertTrue(pipeline["validation"]["bridge_hops_routed"])
        self.assertEqual(
            [hop["governance_packet"]["source"] for hop in pipeline["bridge_hops"]],
            ["swarm", "llm", "predictor"],
        )
        self.assertEqual(pipeline["bridge_hops"][0]["governed_llm"]["status"], "PROPOSED")
        self.assertEqual(pipeline["bridge_hops"][0]["governed_llm"]["packet_type"], "deliberation_request")
        self.assertEqual(pipeline["bridge_hops"][1]["governed_llm"]["status"], "PROPOSED")
        self.assertEqual(pipeline["bridge_hops"][1]["governed_llm"]["packet_type"], "generation_request")
        self.assertNotIn("governed_llm", pipeline["bridge_hops"][2])

    def test_tool_turn_uses_service_lane_without_clogging_direct_lane(self):
        """Tool turns should keep tool call/result traffic off the direct cognitive lane."""
        pipeline = build_governed_turn_pipeline(
            response_mode="operator",
            contract="direct_tool",
            god_brain={
                "strategy_label": "Tool-First Resolution",
                "action_bias": "await_operator_approval",
                "surface_identity": "jarvis",
            },
            tool_result={
                "type": "v9_core",
                "label": "V9 Core",
                "capability": {
                    "module": "v9_core",
                    "action": "generate_scene",
                    "provider": "openrouter",
                },
            },
            runtime_context="operator_runtime",
        )

        self.assertEqual(pipeline["active_lane"], SERVICE_TOOL_LANE)
        self.assertEqual(len(pipeline["service_packets"]), 2)
        self.assertEqual(pipeline["direct_route"], ["gb", "jar"])
        self.assertTrue(all(packet["lane"] == SERVICE_TOOL_LANE for packet in pipeline["service_packets"]))
        self.assertEqual(pipeline["service_packets"][0]["intent"], "tool_call")
        self.assertEqual(pipeline["service_packets"][1]["intent"], "tool_result")
        self.assertEqual(
            pipeline["service_packets"][0]["payload"]["metadata"]["capability_module"],
            "v9_core",
        )
        self.assertEqual(
            pipeline["service_packets"][1]["payload"]["metadata"]["provider"],
            "openrouter",
        )
        self.assertTrue(pipeline["validation"]["tool_traffic_isolated"])
        self.assertTrue(pipeline["validation"]["direct_lane_tool_free"])
        self.assertEqual(pipeline["immune_protocol"]["response"], "ALLOW")
        self.assertTrue(pipeline["validation"]["immune_traffic_allowed"])
        self.assertTrue(all(packet["intent"] not in {"tool_call", "tool_result"} for packet in pipeline["forward_packets"]))
        self.assertEqual(pipeline["capability"]["module"], "v9_core")
        realtime_feed = pipeline["realtime_signal_feed"]
        signal_classes = [signal["signal_class"] for signal in realtime_feed["signals"]]
        predictor = pipeline["realtime_event_cause_predictor"]
        governed_event = pipeline["governed_event"]
        sentinel = pipeline["operator_health_sentinel"]
        self.assertEqual(realtime_feed["runtime_context"], "operator_runtime")
        self.assertEqual(realtime_feed["packet_metrics"]["service_packet_count"], 2)
        self.assertIn("operator_runtime_active", signal_classes)
        self.assertIn("service_lane_active", signal_classes)
        self.assertIn("service_tool_completed", signal_classes)
        self.assertEqual(predictor["cause_class"], "operator_service_request")
        self.assertEqual(predictor["recommended_state"], "proceed")
        self.assertEqual(governed_event["decision"], "ALLOW")
        self.assertEqual(sentinel["operator_state"], "watch")
        self.assertEqual(sentinel["recommended_mode"], "simplify")
        self.assertTrue(all(realtime_feed["validation"].values()))
        self.assertTrue(pipeline["validation"]["bridge_hops_routed"])
        self.assertEqual(
            [hop["governance_packet"]["source"] for hop in pipeline["bridge_hops"]],
            ["swarm", "service_lane", "predictor"],
        )
        self.assertEqual(pipeline["bridge_hops"][0]["governed_llm"]["status"], "PROPOSED")
        self.assertNotIn("governed_llm", pipeline["bridge_hops"][1])
        self.assertNotIn("governed_llm", pipeline["bridge_hops"][2])

    def test_realtime_signal_feed_reports_turn_shift_from_previous_pipeline(self):
        """The feed should surface bounded deltas when the turn changes lanes or tool state."""
        previous_pipeline = build_governed_turn_pipeline(
            response_mode="think",
            contract="gather_plan_answer",
            god_brain={
                "strategy_label": "Council Deliberation",
                "action_bias": "deliberate_then_answer",
                "surface_identity": "jarvis",
            },
            model_route={"id": "local_fast", "label": "Local Fast Route"},
        )

        pipeline = build_governed_turn_pipeline(
            response_mode="operator",
            contract="direct_tool",
            god_brain={
                "strategy_label": "Tool-First Resolution",
                "action_bias": "await_operator_approval",
                "surface_identity": "jarvis",
            },
            tool_result={
                "type": "mystic_reading",
                "status": "completed",
                "capability": {
                    "module": "mystic",
                    "action": "read",
                    "provider": "local_mystic_engine",
                },
            },
            previous_pipeline=previous_pipeline,
        )

        turn_delta = next(
            signal for signal in pipeline["realtime_signal_feed"]["signals"] if signal["signal_type"] == "turn_delta"
        )
        predictor = pipeline["realtime_event_cause_predictor"]
        self.assertEqual(turn_delta["signal_class"], "turn_shift_detected")
        self.assertTrue(turn_delta["attributes"]["lane_changed"])
        self.assertTrue(turn_delta["attributes"]["traffic_class_changed"])
        self.assertTrue(turn_delta["attributes"]["response_mode_changed"])
        self.assertTrue(turn_delta["attributes"]["contract_changed"])
        self.assertTrue(turn_delta["attributes"]["tool_changed"])
        self.assertGreater(turn_delta["attributes"]["change_count"], 0)
        self.assertEqual(predictor["cause_class"], "service_lane_request")
        self.assertEqual(pipeline["governed_event"]["decision"], "ALLOW")

    def test_realtime_signal_feed_reports_stable_repeat_for_identical_turn(self):
        """Repeated identical turn shapes should produce a stable repeat delta."""
        previous_pipeline = build_governed_turn_pipeline(
            response_mode="think",
            contract="gather_plan_answer",
            god_brain={
                "strategy_label": "Council Deliberation",
                "action_bias": "deliberate_then_answer",
                "surface_identity": "jarvis",
            },
            model_route={"id": "local_fast", "label": "Local Fast Route"},
        )

        pipeline = build_governed_turn_pipeline(
            response_mode="think",
            contract="gather_plan_answer",
            god_brain={
                "strategy_label": "Council Deliberation",
                "action_bias": "deliberate_then_answer",
                "surface_identity": "jarvis",
            },
            model_route={"id": "local_fast", "label": "Local Fast Route"},
            previous_pipeline=previous_pipeline,
        )

        turn_delta = next(
            signal for signal in pipeline["realtime_signal_feed"]["signals"] if signal["signal_type"] == "turn_delta"
        )
        predictor = pipeline["realtime_event_cause_predictor"]
        self.assertEqual(turn_delta["signal_class"], "turn_state_stable")
        self.assertTrue(turn_delta["attributes"]["stable_repeat"])
        self.assertEqual(turn_delta["attributes"]["change_count"], 0)
        self.assertEqual(predictor["cause_class"], "steady_state")
        self.assertEqual(predictor["recommended_state"], "proceed")
        self.assertEqual(pipeline["governed_event"]["decision"], "ALLOW")

    def test_realtime_signal_feed_records_immune_boundary_when_protocol_degrades(self):
        """Immune protocol degradation should appear as a bounded signal in the realtime feed."""
        with patch(
            "src.governed_direct_pipeline.apply_immune_protocol",
            return_value={
                "forward_packets": [],
                "service_packets": [],
                "return_packets": [],
                "immune_protocol": {
                    "response": "CLAMP",
                    "traffic_allowed": True,
                    "reasons": ["packet_bloat"],
                    "threats": [{"code": "packet_bloat"}],
                },
            },
        ):
            pipeline = build_governed_turn_pipeline(
                response_mode="think",
                contract="gather_plan_answer",
                god_brain={
                    "strategy_label": "Council Deliberation",
                    "action_bias": "deliberate_then_answer",
                    "surface_identity": "jarvis",
                },
                model_route={"id": "local_fast", "label": "Local Fast Route"},
            )

        realtime_feed = pipeline["realtime_signal_feed"]
        predictor = pipeline["realtime_event_cause_predictor"]
        immune_signal = next(
            signal for signal in realtime_feed["signals"] if signal["signal_type"] == "immune_boundary"
        )
        self.assertEqual(realtime_feed["immune_response"], "CLAMP")
        self.assertEqual(immune_signal["signal_class"], "immune_clamp")
        self.assertEqual(immune_signal["severity"], "medium")
        self.assertEqual(predictor["cause_class"], "immune_guard_intervention")
        self.assertEqual(pipeline["governed_event"]["decision"], "ALLOW")

    def test_governed_event_chain_blocks_invalid_prediction_and_triggers_immune(self):
        invalid_prediction = {
            "module_id": "aais.realtime_event_cause_predictor",
            "version": "0.1",
            "status": "bounded_inference",
            "cause_class": "conflicting_signal_state",
            "confidence": 0.77,
            "supporting_signals": ["turn_shift_detected"],
            "conflict_flags": ["lane_and_tool_tension"],
            "data_sufficiency": "sufficient",
            "recommended_state": "proceed",
            "runtime_context": "live_runtime",
            "source_pipeline_id": "gdp_test",
            "signal_count": 5,
            "phase_gate": {"decision": "ALLOW"},
            "advisory_only": True,
        }

        with patch(
            "src.realtime_event_cause_predictor.interpret_realtime_signal_feed",
            return_value=invalid_prediction,
        ):
            pipeline = build_governed_turn_pipeline(
                response_mode="think",
                contract="gather_plan_answer",
                god_brain={
                    "strategy_label": "Council Deliberation",
                    "action_bias": "deliberate_then_answer",
                    "surface_identity": "jarvis",
                },
                model_route={"id": "local_fast", "label": "Local Fast Route"},
            )

        governed_event = pipeline["governed_event"]
        self.assertEqual(governed_event["decision"], "BLOCK")
        self.assertEqual(governed_event["status"], "blocked")
        self.assertIsInstance(governed_event["immune_action"], dict)
        self.assertTrue(pipeline["validation"]["governed_event_valid"])

    def test_pipeline_envelope_matches_schema_shape(self):
        """Governed turn traces should map to governed_direct_pipeline.v1."""
        pipeline = build_governed_turn_pipeline(
            response_mode="think",
            contract="gather_plan_answer",
            god_brain={
                "strategy_label": "Council Deliberation",
                "action_bias": "deliberate_then_answer",
                "surface_identity": "jarvis",
            },
            model_route={"id": "local_fast", "label": "Local Fast Route"},
        )
        envelope = to_pipeline_envelope(pipeline)
        self.assertEqual(envelope["governed_direct_pipeline_version"], "governed_direct_pipeline.v1")
        self.assertEqual(envelope["turn_id"], pipeline["pipeline_id"])
        self.assertGreaterEqual(len(envelope["lanes"]), 1)
        self.assertGreaterEqual(len(envelope["packets"]), 1)
        self.assertIn(envelope["signal_feed"]["risk_level"], {"low", "medium", "high", "critical"})


class TestGovernedPipelineCache(unittest.TestCase):
    """TTL cache reuses skeleton; per-turn fields still refresh."""

    def setUp(self):
        clear_governed_pipeline_cache()

    def tearDown(self):
        clear_governed_pipeline_cache()

    def test_cache_refreshes_pipeline_id_and_operator_health(self):
        with patch.dict(os.environ, {"AAIS_GOVERNED_PIPELINE_CACHE_SEC": "60"}, clear=False):
            clear_governed_pipeline_cache()
            common = dict(
                response_mode="tiny",
                contract="tiny_companion",
                god_brain={"strategy_label": "companion", "surface_identity": "nova"},
                model_route={"id": "mock_local", "label": "Mock"},
                surface_identity="nova",
            )
            first = build_governed_turn_pipeline(**common, operator_text="hello")
            second = build_governed_turn_pipeline(**common, operator_text="world")
            self.assertNotEqual(first["pipeline_id"], second["pipeline_id"])
            self.assertTrue(first["validation"]["operator_health_sentinel_valid"])
            self.assertTrue(second["validation"]["operator_health_sentinel_valid"])

    def test_cache_disabled_when_ttl_zero(self):
        with patch.dict(os.environ, {"AAIS_GOVERNED_PIPELINE_CACHE_SEC": "0"}, clear=False):
            clear_governed_pipeline_cache()
            kwargs = dict(
                response_mode="fast",
                contract="direct_answer",
                model_route={"id": "local_fast"},
            )
            build_governed_turn_pipeline(**kwargs)
            build_governed_turn_pipeline(**kwargs)
            self.assertEqual(len(_GOVERNED_PIPELINE_CACHE), 0)
