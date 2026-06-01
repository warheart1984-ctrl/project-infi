"""Tests for the Operator Health Sentinel advisory observer."""

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.governed_direct_pipeline import build_governed_turn_pipeline
from src.module_governance import module_governance
from src.operator_health_sentinel import assert_valid_operator_health_snapshot
from src.phase_gate import reset_registry


def _core_pipeline(*, previous_pipeline=None, operator_text=None):
    return build_governed_turn_pipeline(
        response_mode="think",
        contract="gather_plan_answer",
        god_brain={
            "strategy_label": "Council Deliberation",
            "action_bias": "deliberate_then_answer",
            "surface_identity": "jarvis",
        },
        model_route={"id": "local_fast", "label": "Local Fast Route"},
        previous_pipeline=previous_pipeline,
        operator_text=operator_text,
    )


def _service_pipeline(*, previous_pipeline=None, operator_text=None):
    return build_governed_turn_pipeline(
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
        runtime_context="operator_runtime",
        previous_pipeline=previous_pipeline,
        operator_text=operator_text,
    )


class TestOperatorHealthSentinel(unittest.TestCase):
    """Verify bounded operator-load observation and advisory-only behavior."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="operator-health-"))
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        module_governance.configure_runtime_dir(self.temp_root)
        module_governance.reset()
        reset_registry()

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_normal_session_reports_stable_snapshot(self):
        pipeline = _core_pipeline(operator_text="can you summarize this module?")

        snapshot = pipeline["operator_health_sentinel"]

        self.assertEqual(snapshot["operator_state"], "stable")
        self.assertEqual(snapshot["recommended_mode"], "normal")
        self.assertEqual(snapshot["phase_gate"]["decision"], "ALLOW")
        self.assertEqual(snapshot["module_governance"]["decision"], "ALLOW")
        self.assertTrue(snapshot["advisory_only"])
        self.assertEqual(snapshot["execution_rights"], "none")
        self.assertEqual(snapshot["mutation_rights"], "none")
        assert_valid_operator_health_snapshot(snapshot)

    def test_high_manual_arbitration_raises_watch_state(self):
        pipeline = _service_pipeline(
            operator_text="clean fix: move it out of loops and guard it so the lane stays stable",
        )

        snapshot = pipeline["operator_health_sentinel"]

        self.assertGreaterEqual(snapshot["manual_arbitration_score"], 0.5)
        self.assertEqual(snapshot["operator_state"], "watch")
        self.assertEqual(snapshot["recommended_mode"], "simplify")
        self.assertIn("high_manual_arbitration", snapshot["dominant_factors"])
        assert_valid_operator_health_snapshot(snapshot)

    def test_repeated_doctrine_reassertion_raises_drift_pressure(self):
        doctrine_prompt = "advisory-only, bounded, and do not bypass governance."
        previous_pipeline = _core_pipeline(operator_text=doctrine_prompt)
        current_pipeline = _core_pipeline(
            previous_pipeline=previous_pipeline,
            operator_text=doctrine_prompt,
        )

        previous_snapshot = previous_pipeline["operator_health_sentinel"]
        current_snapshot = current_pipeline["operator_health_sentinel"]

        self.assertGreaterEqual(
            current_snapshot["drift_pressure_score"],
            previous_snapshot["drift_pressure_score"],
        )
        self.assertIn("repeated_doctrine_correction", current_snapshot["dominant_factors"])

    def test_high_subsystem_tension_recommends_safe_degrade(self):
        previous_pipeline = _core_pipeline(operator_text="keep the turn direct and bounded")
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
            pipeline = _service_pipeline(
                previous_pipeline=previous_pipeline,
                operator_text="fix the lane and keep the split clean",
            )

        snapshot = pipeline["operator_health_sentinel"]

        self.assertGreaterEqual(snapshot["subsystem_tension_score"], 0.4)
        self.assertEqual(snapshot["recommended_mode"], "safe_degrade")
        self.assertIn("reduce_active_lanes", snapshot["recommended_actions"])

    def test_explicit_overload_increases_confidence_without_forcing_critical(self):
        pipeline = _core_pipeline(
            operator_text="this is too much right now, brain fried, not now",
        )

        snapshot = pipeline["operator_health_sentinel"]

        self.assertIn("explicit_overload_signal", snapshot["dominant_factors"])
        self.assertGreaterEqual(snapshot["confidence"], 0.55)
        self.assertNotEqual(snapshot["operator_state"], "critical")

    def test_one_chaotic_turn_does_not_jump_to_critical(self):
        previous_pipeline = _core_pipeline(operator_text="can you keep this simple?")
        with patch(
            "src.governed_direct_pipeline.apply_immune_protocol",
            return_value={
                "forward_packets": [],
                "service_packets": [],
                "return_packets": [],
                "immune_protocol": {
                    "response": "REJECT",
                    "traffic_allowed": False,
                    "reasons": ["bypass_attempt"],
                    "threats": [{"code": "bypass_attempt"}],
                },
            },
        ):
            pipeline = _service_pipeline(
                previous_pipeline=previous_pipeline,
                operator_text="fix this boundary but do not bypass governance",
            )

        snapshot = pipeline["operator_health_sentinel"]

        self.assertIn(snapshot["operator_state"], {"watch", "strained"})
        self.assertNotEqual(snapshot["operator_state"], "critical")
        assert_valid_operator_health_snapshot(snapshot)

    def test_advisory_only_snapshot_never_mutates_pipeline_behavior(self):
        pipeline = _core_pipeline(operator_text="answer directly")

        snapshot = pipeline["operator_health_sentinel"]

        self.assertEqual(pipeline["active_lane"], "direct_cognitive")
        self.assertTrue(snapshot["advisory_only"])
        self.assertEqual(snapshot["execution_rights"], "none")
        self.assertEqual(snapshot["mutation_rights"], "none")
