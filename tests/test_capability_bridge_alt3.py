"""Capability bridge routes for Alt-3 subsystem families."""

from __future__ import annotations

import unittest

from src.capability_service_bridge import CapabilityServiceBridge
from src.phase_gate import reset_registry


class TestCapabilityBridgeAlt3(unittest.TestCase):
    def setUp(self) -> None:
        reset_registry()

    def _build_bridge(self) -> CapabilityServiceBridge:
        return CapabilityServiceBridge(
            spatial_query=lambda mode, **kwargs: {"mode": mode, "visible": False},
            render_spatial=lambda args, result: "spatial",
            mystic_read=lambda text: {"state": "awakening", "next_action": "go"},
            render_mystic=lambda result: "mystic",
            v9_run=lambda **kwargs: {"status": "completed", "location": "Unknown"},
            render_v9=lambda result: "v9",
            v10_run=lambda **kwargs: {"status": "completed", "location": "Unknown"},
            render_v10=lambda result: "v10",
        )

    def test_snapshot_lists_alt3_capabilities(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        registry = bridge.snapshot()["registry"]
        self.assertIn("recipe_module", registry)
        self.assertIn("imagine_generator", registry)
        self.assertIn("human_voice_extraction", registry)
        imagine_actions = registry["imagine_generator"]
        self.assertIn("emit", imagine_actions)
        self.assertIn("handoff", imagine_actions)
        self.assertIn("grok_render", imagine_actions)

    def test_recipe_create_mission_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        result = bridge.execute_selection(
            "recipe_module",
            "create_mission",
            args={"recipe_id": "onboarding-v1", "signoff_ack": True},
            runtime_context="operator_runtime",
        )
        self.assertEqual(result["tool_result"]["status"], "completed")
        self.assertIn("Operator Onboarding", result["response"])

    def test_imagine_emit_and_handoff_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        emit = bridge.execute_selection(
            "imagine_generator",
            "emit",
            args={"fixture": "scene-seed-demo"},
            runtime_context="operator_runtime",
        )
        self.assertEqual(emit["tool_result"]["status"], "completed")
        pattern_id = emit["tool_result"]["result"]["pattern_id"]
        handoff = bridge.execute_selection(
            "imagine_generator",
            "handoff",
            args={"pattern_id": pattern_id},
            runtime_context="operator_runtime",
        )
        self.assertEqual(handoff["tool_result"]["status"], "completed")

    def test_imagine_grok_render_blocked_without_keys(self) -> None:
        import os

        bridge = self._build_bridge()
        bridge.snapshot()
        for key in ("STORY_FORGE_XAI_API_KEY", "XAI_API_KEY"):
            os.environ.pop(key, None)
        emit = bridge.execute_selection(
            "imagine_generator",
            "emit",
            args={"fixture": "scene-seed-demo"},
            runtime_context="operator_runtime",
        )
        pattern_id = emit["tool_result"]["result"]["pattern_id"]
        grok = bridge.execute_selection(
            "imagine_generator",
            "grok_render",
            args={"pattern_id": pattern_id},
            runtime_context="operator_runtime",
        )
        self.assertIn(grok["tool_result"]["status"], {"failed", "blocked"})

    def test_human_voice_extract_signoff_handoff_via_bridge(self) -> None:
        bridge = self._build_bridge()
        bridge.snapshot()
        extract = bridge.execute_selection(
            "human_voice_extraction",
            "extract",
            args={"fixture": "notes-demo-redacted"},
            runtime_context="operator_runtime",
        )
        self.assertEqual(extract["tool_result"]["status"], "completed")
        extraction_id = extract["tool_result"]["result"]["extraction_id"]
        signoff = bridge.execute_selection(
            "human_voice_extraction",
            "signoff",
            args={"extraction_id": extraction_id, "signoff_by": "operator"},
            runtime_context="operator_runtime",
        )
        self.assertEqual(signoff["tool_result"]["status"], "completed")
        handoff = bridge.execute_selection(
            "human_voice_extraction",
            "handoff",
            args={"extraction_id": extraction_id},
            runtime_context="operator_runtime",
        )
        self.assertEqual(handoff["tool_result"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
