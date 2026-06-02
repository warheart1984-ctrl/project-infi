"""Tests for the governed capability service-lane bridge."""

import unittest

from src.capability_service_bridge import (
    MAX_AUDIT_EVENTS,
    CapabilityServiceBridge,
    to_bridge_envelope,
)
from src.phase_gate import Phase, demote_component, reset_registry


class TestCapabilityServiceBridge(unittest.TestCase):
    """Verify governed capability routing and audit metadata."""

    def setUp(self):
        reset_registry()

    def _build_bridge(self):
        return CapabilityServiceBridge(
            spatial_query=lambda mode, **kwargs: {
                "mode": mode,
                "visible": False,
                "from": kwargs.get("from"),
                "to": kwargs.get("to"),
            },
            render_spatial=lambda args, result: (
                f"Visibility from {args.get('from')} to {args.get('to')}: {result.get('visible')}"
            ),
            mystic_read=lambda text: {
                "state": "awakening",
                "state_label": "Awakening",
                "next_action": "Ship the first step.",
            },
            render_mystic=lambda result: f"Mystic reading: {result['state_label']}",
            v9_run=lambda input_text, context="", location="Unknown", characters=None: {
                "status": "completed",
                "input": input_text,
                "context": context,
                "location": location,
                "characters": list(characters or []),
                "provider": "openrouter",
                "model": "openrouter/free",
                "pipeline": ["DraftAngel"],
                "output": "Scene output",
            },
            render_v9=lambda result: f"V9 Core ran at {result['location']}",
            v10_run=lambda input_text, context="", location="Unknown", characters=None: {
                "status": "completed",
                "input": input_text,
                "context": context,
                "location": location,
                "characters": list(characters or []),
                "provider": "openrouter",
                "model": "openrouter/free",
                "pipeline": ["SceneAngel"],
                "quality_report": {"quality_score": 90},
                "output": "Scene output",
            },
            render_v10=lambda result: f"V10 Core ran at {result['location']}",
        )

    def test_bridge_routes_registered_tool_through_capability_module(self):
        """Successful routed tools should expose capability metadata and audit state."""
        bridge = self._build_bridge()

        result = bridge.handle_tool_request(
            "v9_core",
            {
                "input": "Continue the scene.",
                "context": "The betrayal just landed.",
                "location": "Throne Room",
                "characters": ["Queen Seris", "Captain Vale"],
            },
        )

        self.assertIsNotNone(result)
        tool_result = result["tool_result"]
        self.assertEqual(tool_result["type"], "v9_core")
        self.assertEqual(tool_result["status"], "completed")
        self.assertEqual(tool_result["capability"]["module"], "v9_core")
        self.assertEqual(tool_result["capability"]["action"], "generate_scene")
        self.assertEqual(tool_result["capability"]["provider"], "openrouter")
        self.assertEqual(tool_result["capability"]["model"], "openrouter/free")
        self.assertTrue(tool_result["capability"]["ok"])
        self.assertEqual(bridge.snapshot()["event_count"], 1)
        self.assertEqual(bridge.snapshot()["recent_events"][-1]["tool_type"], "v9_core")

    def test_bridge_normalizes_provider_failures(self):
        """Provider exceptions should become deterministic failed tool results."""
        bridge = CapabilityServiceBridge(
            spatial_query=lambda mode, **kwargs: {"mode": mode, "visible": False},
            render_spatial=lambda args, result: "unused",
            mystic_read=lambda text: {"state": "awakening", "next_action": "Move"},
            render_mystic=lambda result: "unused",
            v9_run=lambda input_text, context="", location="Unknown", characters=None: {
                "status": "completed",
                "location": location,
            },
            render_v9=lambda result: "unused",
            v10_run=lambda input_text, context="", location="Unknown", characters=None: (_ for _ in ()).throw(
                TimeoutError("slow provider")
            ),
            render_v10=lambda result: "unused",
        )

        result = bridge.handle_tool_request("v10_core", {"input": "Continue the scene."})

        self.assertIsNotNone(result)
        tool_result = result["tool_result"]
        self.assertEqual(tool_result["type"], "v10_core")
        self.assertEqual(tool_result["status"], "failed")
        self.assertEqual(tool_result["capability"]["error_type"], "TimeoutError")
        self.assertFalse(tool_result["capability"]["ok"])
        self.assertIn("could not run", result["response"].lower())

    def test_bridge_returns_none_for_unknown_tools(self):
        """Unregistered tools should stay outside the capability bridge."""
        bridge = self._build_bridge()

        self.assertIsNone(bridge.handle_tool_request("workspace_search", {"query": "api.py"}))

    def test_live_runtime_blocks_validated_only_capability(self):
        """Live runtime should fail closed when a capability is no longer active."""
        bridge = self._build_bridge()
        bridge.snapshot()
        demote_component(
            "jarvis.capability.mystic",
            Phase.VALIDATED,
            reason="Keep this path operator-only until final admission.",
            actor="phase_gate_test",
        )

        result = bridge.handle_tool_request(
            "mystic_reading",
            {"input": "I need direction."},
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["tool_result"]["status"], "blocked")
        self.assertEqual(result["phase_gate"]["decision"], "BLOCK")
        self.assertEqual(result["phase_gate"]["component"]["phase"], "validated")
        self.assertEqual(result["phase_gate"]["runtime_context"], "live_runtime")
        self.assertIn("live_runtime", result["phase_gate"]["reason"])

    def test_operator_selection_allows_validated_component_in_guarded_context(self):
        """Operator runtime should still admit validated components on guarded paths."""
        bridge = self._build_bridge()
        bridge.snapshot()
        demote_component(
            "jarvis.capability.mystic",
            Phase.VALIDATED,
            reason="Guarded operator-only admission.",
            actor="phase_gate_test",
        )

        result = bridge.execute_selection(
            "mystic",
            "reading",
            args={"input": "I need direction."},
            execution_profile={"provider_mode": "deterministic", "governance_mode": "strict"},
            runtime_context="operator_runtime",
        )

        self.assertEqual(result["phase_gate"]["decision"], "ALLOW")
        self.assertEqual(result["phase_gate"]["component"]["phase"], "validated")
        self.assertEqual(result["phase_gate"]["runtime_context"], "operator_runtime")
        self.assertEqual(result["tool_result"]["status"], "completed")

    def test_bridge_envelope_matches_schema_shape(self):
        """Bridge snapshots should map to capability_service_bridge.v1."""
        bridge = self._build_bridge()
        bridge.handle_tool_request("v9_core", {"input": "Continue the scene."})
        envelope = to_bridge_envelope(bridge.snapshot())
        self.assertEqual(envelope["capability_service_bridge_version"], "capability_service_bridge.v1")
        self.assertEqual(envelope["component_id"], "jarvis.capability_service_bridge")
        self.assertIn(envelope["governance_mode"], {"strict", "assist", "experimental"})
        self.assertGreaterEqual(len(envelope["service_path"]), 1)
        self.assertIn("capability_call", envelope)

    def test_audit_ring_is_bounded(self):
        """Audit events must stay within MAX_AUDIT_EVENTS."""
        bridge = self._build_bridge()
        for index in range(MAX_AUDIT_EVENTS + 5):
            bridge.handle_tool_request(
                "v9_core",
                {"input": f"Scene beat {index}."},
            )
        self.assertLessEqual(bridge.snapshot()["event_count"], MAX_AUDIT_EVENTS)


if __name__ == "__main__":
    unittest.main()
