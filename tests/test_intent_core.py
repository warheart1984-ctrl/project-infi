"""Tests for Nova Intent Core — commitments, tensions, agency."""

import unittest
from types import SimpleNamespace

from src.cog_runtime.intent_core import (
    CONSTITUTIONAL_PROTECTED_VALUES,
    intent_context_for_lobes,
    intent_module_spec,
    run_intent_turn,
    validate_intent_artifact,
)


def _cog_session(**artifacts):
    return SimpleNamespace(
        artifacts=dict(artifacts),
        frame_kind="decision",
    )


class TestIntentCore(unittest.TestCase):
    def test_module_spec_has_capability_contract(self):
        spec = intent_module_spec()
        self.assertEqual(spec["id"], "nova.intent")
        self.assertEqual(spec["version"], "0.2")
        for field in ("capability_metric", "baseline_substitute", "evidence_status", "sunset_trigger"):
            self.assertTrue(str(spec.get(field) or "").strip())

    def test_validate_requires_protected_values(self):
        artifact = {
            "active_commitments": [],
            "protected_values": [],
            "long_horizon_goals": [],
            "current_tensions": [{"poles": ["a", "b"], "pull": "a", "reason": "test"}],
            "agency_note": "hold",
        }
        result = validate_intent_artifact(artifact)
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing_protected_value" in issue for issue in result["issues"]))

    def test_run_intent_turn_infers_decision_tension(self):
        session = _cog_session(
            decision_object={"alternatives": ["fast", "safe"], "chosen_option": "safe"},
            cognitive_arc={"goal_type": "general", "turn_count": 1},
            reflection_artifact={"alignment": "aligned"},
            planning_artifact={"next_action": "Document proof gap"},
            execution_artifact={},
        )
        artifact = run_intent_turn(cog_session=session)
        self.assertTrue(validate_intent_artifact(artifact)["valid"])
        poles = [t["poles"] for t in artifact["current_tensions"]]
        self.assertTrue(any("certainty" in p and "curiosity" in p for p in poles))
        self.assertEqual(artifact["active_commitments"][0]["commitment"], "Document proof gap")

    def test_commitments_survive_prior_when_story_would_change(self):
        prior = {
            "active_commitments": [
                {"commitment": "Finish cross-machine proof", "status": "active", "source": "operator"}
            ],
            "long_horizon_goals": ["Persistent continuity"],
            "protected_values": list(CONSTITUTIONAL_PROTECTED_VALUES),
            "current_tensions": [],
            "agency_note": "prior",
        }
        session = _cog_session(
            cognitive_arc={"goal_type": "exploration", "turn_count": 3, "root_goal": "New arc goal"},
            decision_object={},
            reflection_artifact={"alignment": "partial", "adjustments": ["Tighten verification"]},
            planning_artifact={"next_action": "Run wolf reboot fixture"},
            execution_artifact={},
        )
        artifact = run_intent_turn(cog_session=session, prior_intent=prior)
        commitments = [c["commitment"] for c in artifact["active_commitments"]]
        self.assertIn("Finish cross-machine proof", commitments)
        self.assertIn("Run wolf reboot fixture", commitments)

    def test_intent_context_for_lobes_read_only(self):
        artifact = run_intent_turn(
            cog_session=_cog_session(
                cognitive_arc={"turn_count": 2},
                reflection_artifact={},
                planning_artifact={"next_action": "Hold agency"},
                execution_artifact={},
            )
        )
        ctx = intent_context_for_lobes(artifact)
        self.assertIn("intent_commitments", ctx)
        self.assertIn("intent_tensions", ctx)
        self.assertIn("intent_agency_note", ctx)
        self.assertEqual(ctx, intent_context_for_lobes(artifact))


if __name__ == "__main__":
    unittest.main()
