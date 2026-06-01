"""Tests for Nova Coherence Projection — voice speaks from cortex state."""

import unittest

from src.cog_runtime.coherence_projection import (
    build_coherence_projection,
    format_coherence_projection_block,
)
from src.jarvis_modular import build_context_modules


class TestCoherenceProjection(unittest.TestCase):
    def test_builds_projection_from_session_metadata(self):
        metadata = {
            "cognitive_runtime_enabled": True,
            "nova_intent": {
                "agency_note": "Still committed to proof while pulled toward safety.",
                "current_tensions": [{"poles": ["safety", "exploration"], "pull": "safety"}],
                "active_commitments": [
                    {"commitment": "Finish cross-machine proof", "status": "active", "claim_posture": "asserted"}
                ],
                "continuity_claim_posture": "asserted",
                "long_horizon_goals": [{"goal": "Persistent continuity", "claim_posture": "asserted"}],
            },
            "nova_narrative": {
                "active_story": "Helping forge Wolf Cog OS",
                "becoming": "improving continuity; pulled toward safety",
                "working_on": "Cross-machine proof",
                "current_chapter": "Intent agency",
            },
            "cortex_arc": {"root_goal": "Ship continuity", "goal_type": "continuity", "turn_count": 2},
            "cognitive_runtime_artifacts": {
                "focus_artifact": {"primary_focus": "cross-machine proof"},
                "decision_object": {"chosen_option": "Take the safe verified path", "rationale": "Governance first."},
                "planning_artifact": {"next_action": "Run wolf reboot fixture"},
            },
        }
        projection = build_coherence_projection(metadata)
        self.assertIsNotNone(projection)
        self.assertTrue(projection["read_only"])
        self.assertEqual(projection["intent"]["active_commitments"][0]["commitment"], "Finish cross-machine proof")
        self.assertEqual(projection["cognition"]["next_action"], "Run wolf reboot fixture")
        block = format_coherence_projection_block(projection)
        self.assertIn("Speak from this cognitive state", block)
        self.assertIn("Finish cross-machine proof", block)

    def test_skips_when_cognitive_runtime_disabled(self):
        self.assertIsNone(build_coherence_projection({"cognitive_runtime_enabled": False}))

    def test_modular_pipeline_injects_cognitive_module(self):
        modules, _ = build_context_modules(
            [{"role": "user", "content": "What should we do next?"}],
            metadata={
                "cognitive_runtime_enabled": True,
                "nova_intent": {
                    "agency_note": "Hold agency.",
                    "current_tensions": [],
                    "active_commitments": [],
                    "continuity_claim_posture": "asserted",
                },
                "nova_narrative": {"active_story": "Proof work", "becoming": "steady", "working_on": "proof"},
                "cortex_arc": {"root_goal": "Proof", "goal_type": "general", "turn_count": 1},
                "cognitive_runtime_artifacts": {
                    "planning_artifact": {"next_action": "Continue proof harness"},
                },
            },
        )
        channels = [module.get("channel") for module in modules]
        self.assertIn("cognitive", channels)
        cognitive = next(module for module in modules if module.get("channel") == "cognitive")
        self.assertEqual(cognitive.get("source_module"), "NovaCoherenceProjectionModule")
        self.assertIn("Continue proof harness", cognitive.get("content", ""))


if __name__ == "__main__":
    unittest.main()
