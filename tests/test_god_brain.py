"""Tests for the sovereign God Brain turn orchestrator."""

import unittest

from src.god_brain import build_god_brain_trace
from src.specialist_registry import detect_specialist_profile


class TestGodBrain(unittest.TestCase):
    """Verify the orchestration trace is stable and informative."""

    def test_debug_turn_builds_fault_isolation_council(self):
        """Debug requests should produce a fault-isolation strategy with a specialist lead."""
        profile = detect_specialist_profile(
            "Debug this traceback in api.py and tell me which pytest to run next.",
            current_mode="debug",
        )

        trace = build_god_brain_trace(
            user_message="Debug this traceback in api.py and tell me which pytest to run next.",
            response_mode="debug",
            current_goal="find the real break point",
            contract="trace_isolate_verify",
            specialist_profile=profile,
            memory_count=2,
            workspace_hits=4,
            research_sources=0,
            policy_status={"posture": "nominal"},
        )

        self.assertEqual(trace["strategy_label"], "Fault Isolation Council")
        self.assertEqual(trace["lead"]["label"], "Debug")
        self.assertEqual(trace["action_bias"], "inspect_local_artifacts")
        self.assertEqual(trace["council"][0]["label"], "Sovereign Core")
        self.assertIn("Workspace", [step["label"] for step in trace["execution_path"]])
        self.assertIn("Plan", [step["label"] for step in trace["execution_path"]])
        self.assertIn("concrete failure signals", trace["arbiter"]["rule"].lower())

    def test_tool_first_trace_holds_on_approval_boundary(self):
        """Action requests should become approval-first God Brain traces."""
        trace = build_god_brain_trace(
            user_message="Run pytest for me.",
            response_mode="operator",
            current_goal="verify the current backend state",
            contract="direct_tool",
            requested_specialists=["debugging", "testing"],
            tool_type="action_request",
            tool_label="Run Pytest",
            policy_status={"posture": "cautious"},
        )

        self.assertEqual(trace["strategy_id"], "tool_first_resolution")
        self.assertEqual(trace["action_bias"], "await_operator_approval")
        self.assertEqual(trace["lead"]["label"], "Debug")
        self.assertIn("approval boundary", trace["arbiter"]["rule"].lower())
        self.assertIn("Tool", [step["label"] for step in trace["execution_path"]])
