"""Capability bridge integration with Alt-7 coherence fabric enforcement."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.adaptive_lane_organ import LaneResolution
from src.capability_service_bridge import CapabilityServiceBridge
from src.phase_gate import reset_registry


REPO = Path(__file__).resolve().parents[1]


class TestCoherenceFabricBridge(unittest.TestCase):
    def setUp(self):
        reset_registry()

    def _build_bridge(self) -> CapabilityServiceBridge:
        return CapabilityServiceBridge(
            spatial_query=lambda mode, **kwargs: {"mode": mode, "visible": False},
            render_spatial=lambda args, result: "unused",
            mystic_read=lambda text: {"state": "awakening", "next_action": "Move"},
            render_mystic=lambda result: "unused",
            v9_run=lambda input_text, context="", location="Unknown", characters=None: {
                "status": "completed",
                "location": location,
            },
            render_v9=lambda result: "unused",
            v10_run=lambda input_text, context="", location="Unknown", characters=None: {
                "status": "completed",
                "location": location,
            },
            render_v10=lambda result: "unused",
        )

    def _recipe_spec(
        self,
        *,
        capability_id: str,
        handler,
        action: str | None = None,
        action_label: str | None = None,
    ):
        if action is None:
            if capability_id == "approve_policy_changes":
                action = "approve"
                action_label = action_label or "Approve Policy"
            else:
                action = "create_mission"
                action_label = action_label or "Create Mission"
        else:
            action_label = action_label or action.replace("_", " ").title()
        return {
            "capability_id": capability_id,
            "capability_label": "Recipe Module",
            "tool": "recipe_module",
            "gene": "recipe_module",
            "action": action,
            "action_label": action_label,
            "module": SimpleNamespace(module_name="recipe_module"),
            "handler": handler,
        }

    def _register_test_route(self, bridge, spec):
        bridge._selection_routes[(spec["capability_id"], spec["action"])] = spec

    def _run_spec(self, bridge, spec):
        self._register_test_route(bridge, spec)
        with patch(
            "src.adaptive_lane_organ.resolve_lane_for_gene",
            return_value=LaneResolution(
                lane_id="operator",
                weight=1.0,
                capabilities=("approve_policy_changes",),
                gene="recipe_module",
            ),
        ):
            with patch(
                "src.governance_organs.adaptive_engine.AdaptiveEngine.evaluate_context",
                return_value=type("R", (), {"blocked": False})(),
            ):
                with patch.object(bridge, "_evaluate_phase_gate", return_value={"decision": "ALLOW"}):
                    with patch.object(bridge, "_prepare_args_for_selection", side_effect=lambda s, a: a):
                        return bridge._execute_spec(
                            spec,
                            {},
                            runtime_context="operator_runtime",
                        )

    def test_execute_spec_blocks_when_fabric_misaligned(self):
        bridge = self._build_bridge()
        spec = self._recipe_spec(
            capability_id="recipe_module",
            handler=lambda *args, **kwargs: {"response": "should not run"},
        )

        with patch(
            "src.operator_cognition_coherence_fabric.coherence_inputs_for_bridge",
            return_value=("strict", LaneResolution(lane_id="operator", weight=1.0, capabilities=()), False, False),
        ):
            result = self._run_spec(bridge, spec)

        self.assertEqual(result["tool_result"]["status"], "blocked")
        self.assertIn("misaligned", result["response"].lower())

    def test_execute_spec_blocks_policy_cap_under_non_strict_mode(self):
        bridge = self._build_bridge()
        spec = self._recipe_spec(
            capability_id="approve_policy_changes",
            handler=lambda *args, **kwargs: {"response": "should not run"},
        )

        with patch(
            "src.operator_cognition_coherence_fabric.coherence_inputs_for_bridge",
            return_value=("assist", LaneResolution(lane_id="operator", weight=1.0, capabilities=("approve_policy_changes",)), True, False),
        ):
            result = self._run_spec(bridge, spec)

        self.assertEqual(result["tool_result"]["status"], "blocked")
        self.assertIn("strict", result["response"].lower())

    def test_execute_spec_allows_non_policy_capability_when_fabric_aligned(self):
        bridge = self._build_bridge()
        called = {"value": False}

        def handler(args, **kwargs):
            called["value"] = True
            return {"response": "ok", "tool_result": {"status": "completed"}}

        spec = self._recipe_spec(capability_id="recipe_module", handler=handler)

        with patch(
            "src.operator_cognition_coherence_fabric.coherence_inputs_for_bridge",
            return_value=("strict", LaneResolution(lane_id="operator", weight=1.0, capabilities=("approve_policy_changes",)), True, False),
        ):
            result = self._run_spec(bridge, spec)

        self.assertTrue(called["value"])
        self.assertEqual(result["response"], "ok")


if __name__ == "__main__":
    unittest.main()
