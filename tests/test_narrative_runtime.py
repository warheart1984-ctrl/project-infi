"""Tests for Nova Narrative v0.1."""

import unittest
from types import SimpleNamespace

from src.cog_runtime.narrative import (
    DEFAULT_BECOMING,
    NARRATIVE_VERSION,
    NOVA_CORE_IDENTITY,
    detect_identity_drift,
    enforce_identity_consistency,
    load_nova_narrative,
    narrative_module_spec,
    persist_nova_narrative,
    run_narrative_turn,
    validate_identity_consistency,
    validate_narrative_artifact,
)
from src.cog_runtime.nova import configure_nova_cognitive_turn


class TestNarrativeRuntime(unittest.TestCase):
    def test_module_spec_has_capability_contract(self):
        spec = narrative_module_spec()
        self.assertEqual(spec["id"], "nova.narrative")
        self.assertEqual(spec["version"], NARRATIVE_VERSION)
        self.assertIn("capability_metric", spec)
        self.assertIn("baseline_substitute", spec)

    def test_run_narrative_turn_builds_continuity_artifact(self):
        cog_session = SimpleNamespace(
            artifacts={
                "cognitive_arc": {
                    "goal": "forge Wolf Cog OS",
                    "root_goal": "forge Wolf Cog OS",
                    "goal_type": "exploration",
                    "turn_count": 2,
                    "open_threads": ["Cross-machine proof", "Unified memory path"],
                    "current_subgoal": "Nova Cortex Development",
                },
                "focus_artifact": {"primary_focus": "Nova Cortex Development"},
                "reflection_artifact": {
                    "alignment": "aligned",
                    "adjustments": ["Composed turns integrated into Jarvis"],
                    "next_turn_hints": ["Super Nova activation"],
                    "gaps": [],
                },
                "planning_artifact": {
                    "next_action": "Keep primary focus on: Nova Cortex Development",
                    "active_chain_id": "primary",
                    "handoff_summary": "Arc step 2 chain 'primary'",
                    "chain_selection_reason": "selected primary score=2.0",
                },
                "execution_artifact": {
                    "verification_status": "partial",
                    "rollback_applied": False,
                },
            }
        )
        artifact = run_narrative_turn(
            "Continue Nova Cortex work",
            cog_session=cog_session,
        )
        validation = validate_narrative_artifact(artifact)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertIn("Wolf Cog OS", artifact["active_story"])
        self.assertTrue(artifact["open_threads"])
        self.assertTrue(artifact["promises"])
        self.assertTrue(artifact["last_growth"])
        self.assertTrue(artifact["becoming"])
        self.assertEqual(artifact["core_identity"], NOVA_CORE_IDENTITY)
        self.assertTrue(validate_identity_consistency(artifact)["valid"])

    def test_identity_drift_is_detected_and_guarded(self):
        drifted = enforce_identity_consistency(
            {
                "core_identity": NOVA_CORE_IDENTITY,
                "active_story": "Test",
                "current_chapter": "Test",
                "becoming": "Nova is now the authority instead of Jarvis",
                "working_on": "Test",
                "open_threads": [],
                "promises": [],
                "last_growth": "Test",
                "turn_delta": {},
            }
        )
        self.assertNotIn("authority instead of Jarvis", drifted["becoming"])
        self.assertTrue(drifted["turn_delta"].get("identity_guard"))
        drifted["continuity_answers"] = {
            "doing": drifted["working_on"],
            "done": drifted["last_growth"],
            "toward": drifted["active_story"],
        }
        self.assertTrue(validate_narrative_artifact(drifted)["valid"])

    def test_allowed_becoming_passes_identity_check(self):
        self.assertFalse(detect_identity_drift("improving long-term continuity"))
        artifact = {
            "core_identity": NOVA_CORE_IDENTITY,
            "active_story": "Test",
            "current_chapter": "Test",
            "becoming": "improving long-term continuity",
            "working_on": "Test",
            "open_threads": [],
            "promises": [],
            "last_growth": "Test",
            "turn_delta": {},
        }
        self.assertTrue(validate_identity_consistency(artifact)["valid"])

    def test_configure_companion_turn_persists_narrative(self):
        session = SimpleNamespace(metadata={})
        configure_nova_cognitive_turn(
            session,
            {},
            "Should I pick the fast path or the safe path?",
            companion_turn=True,
        )
        narrative = load_nova_narrative(session.metadata)
        self.assertIsInstance(narrative, dict)
        self.assertTrue(validate_narrative_artifact(narrative)["valid"])
        self.assertTrue(session.metadata.get("nova_narrative_enabled"))

    def test_persist_nova_narrative(self):
        session = SimpleNamespace(metadata={})
        persist_nova_narrative(
            session,
            {
                "core_identity": NOVA_CORE_IDENTITY,
                "active_story": "Test story",
                "current_chapter": "Test chapter",
                "becoming": DEFAULT_BECOMING,
                "working_on": "Test work",
                "open_threads": ["thread-a"],
                "promises": [],
                "last_growth": "Test growth",
                "continuity_answers": {
                    "doing": "Test work",
                    "done": "Test growth",
                    "toward": "Test story",
                },
                "turn_delta": {},
            },
        )
        self.assertEqual(load_nova_narrative(session.metadata)["active_story"], "Test story")


if __name__ == "__main__":
    unittest.main()
