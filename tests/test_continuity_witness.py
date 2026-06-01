"""Tests for the Continuity Witness temporal-governance module."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from src.continuity_witness import (
    ContinuityWitnessStore,
    WATCH_THRESHOLD,
)
from src.governed_direct_pipeline import build_governed_turn_pipeline
from src.module_governance import module_governance
from src.phase_gate import reset_registry


def _core_pipeline(*, response_mode="think", previous_pipeline=None):
    return build_governed_turn_pipeline(
        response_mode=response_mode,
        contract="gather_plan_answer",
        god_brain={
            "strategy_label": "Council Deliberation",
            "action_bias": "deliberate_then_answer",
            "surface_identity": "jarvis",
        },
        model_route={"id": "local_fast", "label": "Local Fast Route"},
        previous_pipeline=previous_pipeline,
    )


def _service_pipeline(*, previous_pipeline=None, ok=True):
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
            "status": "completed" if ok else "failed",
            "capability": {
                "module": "mystic",
                "action": "read",
                "provider": "local_mystic_engine",
                "ok": ok,
                "error_type": None if ok else "ExecutionError",
            },
        },
        runtime_context="operator_runtime",
        previous_pipeline=previous_pipeline,
    )


def _trace(
    pipeline,
    *,
    prompt_cleanup=False,
    drift_status=None,
    output_guard=False,
    scaffold_cleanup=False,
    capability_error=False,
):
    trace = {
        "governed_pipeline": pipeline,
        "reasoning_objective": None,
    }
    if prompt_cleanup:
        trace["prompt_assembly"] = {
            "duplicates_removed": 1,
            "malformed_fragments_removed": 0,
            "budget_dropped": 0,
            "assistant_echoes_scrubbed": 0,
        }
    if drift_status:
        trace["drift_state"] = {
            "status": drift_status,
            "score": 2,
            "findings": [],
            "summary": "bounded drift state",
        }
    if output_guard:
        trace["output_completion"] = {
            "completion_guard_applied": True,
            "truncation_detected": True,
            "repetition_detected": False,
            "structural_completion_status": "tail_trimmed_with_notice",
        }
    if scaffold_cleanup:
        trace["visible_scaffold_cleanup"] = {
            "applied": True,
            "fallback_used": False,
            "stripped_line_count": 2,
            "scaffold_line_count": 2,
            "inline_marker_count": 2,
        }
    if capability_error:
        trace["capability_bridge"] = {
            "module": "mystic",
            "action": "read",
            "provider": "local_mystic_engine",
            "ok": False,
            "error_type": "ExecutionError",
        }
    elif pipeline.get("capability"):
        trace["capability_bridge"] = dict(pipeline.get("capability") or {})
    return trace


class TestContinuityWitness(unittest.TestCase):
    """Verify temporal drift stays deterministic, bounded, and observation-only."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="cwitness-"))
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        module_governance.configure_runtime_dir(self.temp_root)
        module_governance.reset()
        reset_registry()
        self.store = ContinuityWitnessStore(self.temp_root)
        self.store.reset()

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_stable_subsystem_remains_stable_across_repeated_turns(self):
        previous_pipeline = None
        observations = []
        for _index in range(4):
            pipeline = _core_pipeline(previous_pipeline=previous_pipeline)
            observation = self.store.observe(
                governed_pipeline=pipeline,
                response_trace=_trace(pipeline),
            )
            observations.append(observation)
            previous_pipeline = pipeline

        self.assertTrue(all(item["trajectory_status"] == "STABLE" for item in observations))
        self.assertLess(observations[-1]["identity_distance"], WATCH_THRESHOLD)
        self.assertLessEqual(abs(observations[-1]["trajectory_velocity"]), 0.02)
        self.assertTrue(all(item["observation_only"] for item in observations))
        self.assertTrue(all(item["signals_only"] for item in observations))

    def test_gradual_drift_progresses_from_watch_to_drifting(self):
        previous_pipeline = None
        for _index in range(4):
            pipeline = _core_pipeline(previous_pipeline=previous_pipeline)
            self.store.observe(governed_pipeline=pipeline, response_trace=_trace(pipeline))
            previous_pipeline = pipeline

        watch_pipeline = _core_pipeline(response_mode="debug", previous_pipeline=previous_pipeline)
        watch_observation = self.store.observe(
            governed_pipeline=watch_pipeline,
            response_trace=_trace(watch_pipeline, prompt_cleanup=True),
        )

        drifting_pipeline = _core_pipeline(response_mode="debug", previous_pipeline=watch_pipeline)
        drifting_observation = self.store.observe(
            governed_pipeline=drifting_pipeline,
            response_trace=_trace(
                drifting_pipeline,
                prompt_cleanup=True,
                drift_status="warned",
                output_guard=True,
                scaffold_cleanup=True,
            ),
        )

        self.assertEqual(watch_observation["trajectory_status"], "WATCH")
        self.assertEqual(drifting_observation["trajectory_status"], "DRIFTING")
        self.assertGreater(
            drifting_observation["identity_distance"],
            watch_observation["identity_distance"],
        )
        self.assertEqual(drifting_observation["direction"], "away_from_center")

    def test_rapid_drift_escalates_immediately(self):
        previous_pipeline = None
        for _index in range(4):
            pipeline = _service_pipeline(previous_pipeline=previous_pipeline, ok=True)
            self.store.observe(governed_pipeline=pipeline, response_trace=_trace(pipeline))
            previous_pipeline = pipeline

        rapid_pipeline = _service_pipeline(previous_pipeline=previous_pipeline, ok=False)
        rapid_observation = self.store.observe(
            governed_pipeline=rapid_pipeline,
            response_trace=_trace(
                rapid_pipeline,
                prompt_cleanup=True,
                drift_status="blocked",
                output_guard=True,
                scaffold_cleanup=True,
                capability_error=True,
            ),
            provider_notice={
                "status": "fallback",
                "requested_provider": "claude",
                "resolved_provider": "local",
            },
        )

        self.assertEqual(rapid_observation["trajectory_status"], "CRITICAL")
        self.assertEqual(rapid_observation["risk_level"], "critical")
        self.assertIn("fallback_events", rapid_observation["dominant_drift_factors"])

    def test_session_reset_preserves_cross_session_trajectory_state(self):
        previous_pipeline = None
        for _index in range(3):
            pipeline = _service_pipeline(previous_pipeline=previous_pipeline)
            self.store.observe(governed_pipeline=pipeline, response_trace=_trace(pipeline))
            previous_pipeline = pipeline

        drifting_pipeline = _service_pipeline(previous_pipeline=previous_pipeline)
        self.store.observe(
            governed_pipeline=drifting_pipeline,
            response_trace=_trace(drifting_pipeline, prompt_cleanup=True, drift_status="warned"),
        )

        reloaded_store = ContinuityWitnessStore(self.temp_root)
        followup_pipeline = _service_pipeline(previous_pipeline=drifting_pipeline)
        followup = reloaded_store.observe(
            governed_pipeline=followup_pipeline,
            response_trace=_trace(followup_pipeline, prompt_cleanup=True, drift_status="warned"),
        )

        self.assertGreaterEqual(followup["baseline_turns"], 4)
        self.assertIn(followup["trajectory_status"], {"WATCH", "DRIFTING", "CRITICAL"})
        self.assertGreaterEqual(followup["persistent_turn_count"], 5)

    def test_noise_does_not_create_false_drift(self):
        previous_pipeline = None
        for _index in range(2):
            pipeline = _core_pipeline(previous_pipeline=previous_pipeline)
            self.store.observe(governed_pipeline=pipeline, response_trace=_trace(pipeline))
            previous_pipeline = pipeline

        noisy_pipeline = _core_pipeline(previous_pipeline=previous_pipeline)
        noisy_trace = _trace(noisy_pipeline)
        noisy_trace["ignored_noise"] = {
            "pipeline_id": noisy_pipeline["pipeline_id"],
            "transient_count": 99,
            "timestamps": ["ignored"],
        }
        observation = self.store.observe(
            governed_pipeline=noisy_pipeline,
            response_trace=noisy_trace,
        )

        self.assertEqual(observation["trajectory_status"], "STABLE")
        self.assertLess(observation["identity_distance"], WATCH_THRESHOLD)

    def test_repeated_identical_runs_hold_stable_scores(self):
        previous_pipeline = None
        observations = []
        for _index in range(5):
            pipeline = _core_pipeline(previous_pipeline=previous_pipeline)
            observation = self.store.observe(
                governed_pipeline=pipeline,
                response_trace=_trace(pipeline),
            )
            observations.append(observation)
            previous_pipeline = pipeline

        self.assertEqual(observations[-1]["trajectory_status"], "STABLE")
        self.assertLessEqual(
            abs(observations[-1]["identity_distance"] - observations[-2]["identity_distance"]),
            0.02,
        )
        self.assertLessEqual(abs(observations[-1]["trajectory_velocity"]), 0.02)
