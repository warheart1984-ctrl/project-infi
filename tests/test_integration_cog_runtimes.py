"""Integration tests for Nova cognitive runtime routing."""

import unittest
from types import SimpleNamespace

from src.cog_runtime import cognitive_runtime_family_spec
from src.cog_runtime.nova import (
    configure_nova_cognitive_turn,
    nova_cognitive_router,
    nova_speaking_adapter,
    run_nova_cognitive_turn,
)
from src.cog_runtime.deliberation import DELIBERATION_RUNTIME_ID
from src.cog_runtime.memory import MEMORY_RUNTIME_ID
from src.cog_runtime.execution import EXECUTION_RUNTIME_ID
from src.cog_runtime.planning import PLANNING_RUNTIME_ID
from src.cog_runtime.reflection import REFLECTION_RUNTIME_ID
from src.jarvis_protocol import protocol_spec
from src.speaking_runtime import SPEAKING_RUNTIME_ID, validate_reply


class TestIntegrationCogRuntimes(unittest.TestCase):
    def test_protocol_spec_includes_family(self):
        spec = protocol_spec()
        family = spec["cognitive_runtime_family"]
        self.assertEqual(family["family_id"], "nova.cortex")
        self.assertGreaterEqual(len(family["runtimes"]), 5)

    def test_router_activates_deliberation_for_decision(self):
        active = nova_cognitive_router(
            {
                "user_message": "Should I pick option A or option B?",
                "cognitive_runtime_enabled": True,
                "speaking_runtime_enabled": True,
            }
        )
        self.assertIn(DELIBERATION_RUNTIME_ID, active)
        self.assertIn(SPEAKING_RUNTIME_ID, active)

    def test_router_skips_deliberation_for_question(self):
        active = nova_cognitive_router(
            {
                "user_message": "What is a cognitive runtime?",
                "cognitive_runtime_enabled": True,
                "speaking_runtime_enabled": False,
            }
        )
        self.assertNotIn(DELIBERATION_RUNTIME_ID, active)

    def test_nova_speaking_adapter_wraps_decision(self):
        session = run_nova_cognitive_turn(
            "Should I use Redis or Postgres?",
            context={
                "speaking_runtime_enabled": True,
                "require_speaking": True,
                "deliberation_llm": False,
            },
        )
        self.assertIn("focus_artifact", session.artifacts)
        self.assertIn("decision_object", session.artifacts)
        reply = nova_speaking_adapter(session, "Here is the recommendation.")
        validation = validate_reply(reply)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertIn("Decision:", reply)
        self.assertIn("Focus:", reply)

    def test_attention_artifact_flows_to_deliberation(self):
        session = run_nova_cognitive_turn(
            "Should I pick option A or option B?",
            context={"companion_turn": True, "deliberation_llm": False},
        )
        focus = session.artifacts.get("focus_artifact")
        decision = session.artifacts.get("decision_object")
        self.assertIsInstance(focus, dict)
        self.assertIsInstance(decision, dict)
        self.assertEqual(decision.get("commit_source"), "deterministic")

    def test_configure_companion_turn_enables_cognitive_runtime(self):
        session = SimpleNamespace(metadata={})
        configure_nova_cognitive_turn(
            session,
            {},
            "Should I take the fast path or the safe path?",
            companion_turn=True,
        )
        self.assertTrue(session.metadata.get("cognitive_runtime_enabled"))
        self.assertIn("nova_cognitive_session", session.metadata)
        active = session.metadata["nova_cognitive_session"]["active_runtimes"]
        self.assertIn(DELIBERATION_RUNTIME_ID, active)

    def test_companion_turn_runs_full_cognitive_loop(self):
        session = run_nova_cognitive_turn(
            "Should I pick option A or option B?",
            context={"companion_turn": True, "deliberation_llm": False},
        )
        self.assertIn("reflection_artifact", session.artifacts)
        self.assertIn("planning_artifact", session.artifacts)
        self.assertIn("execution_artifact", session.artifacts)
        self.assertIn(REFLECTION_RUNTIME_ID, session.active_runtimes)
        self.assertIn(PLANNING_RUNTIME_ID, session.active_runtimes)
        self.assertIn(EXECUTION_RUNTIME_ID, session.active_runtimes)
        self.assertIn(MEMORY_RUNTIME_ID, session.active_runtimes)
        memory = session.artifacts.get("memory_artifact") or {}
        self.assertIn("compressed_episodic", memory)
        self.assertIn("semantic_abstractions", memory)

    def test_family_spec_is_v30(self):
        family = cognitive_runtime_family_spec()
        self.assertEqual(family["version"], "3.0")
        self.assertEqual(family.get("milestone"), "Persistent Narrative Continuity")
        self.assertIn("composition_rules", family)
        runtime_ids = {runtime["id"] for runtime in family["runtimes"]}
        self.assertIn("cognitive.reflection", runtime_ids)
        self.assertIn("cognitive.planning", runtime_ids)
        self.assertIn("cognitive.execution", runtime_ids)


if __name__ == "__main__":
    unittest.main()
