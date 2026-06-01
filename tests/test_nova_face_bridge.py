"""Tests for Nova Face → Nova Cortex → Jarvis Core bridge."""

import unittest
from types import SimpleNamespace

from src.cog_runtime.nova_face import (
    bridge_nova_face_to_cortex_and_jarvis,
    build_jarvis_core_binding,
    resolve_nova_face,
)


def _session(**metadata):
    return SimpleNamespace(metadata=dict(metadata))


TINY_PROFILE = {
    "identity": "tiny_nova",
    "label": "Tiny Nova",
    "response_mode": "tiny",
    "continuity_profile": {
        "scope": "tiny_nova",
        "tone": "light",
        "self_description": "Tiny Nova keeps the conversation brief.",
    },
}


class TestNovaFaceBridge(unittest.TestCase):
    def test_resolve_tiny_nova_face(self):
        face = resolve_nova_face(
            persona_mode="tiny_nova",
            response_mode="tiny",
            companion_turn=True,
            surface_profile=TINY_PROFILE,
        )
        self.assertEqual(face.face_id, "tiny_nova")
        self.assertEqual(face.label, "Tiny Nova")
        self.assertTrue(face.companion_turn)

    def test_bridge_companion_turn_runs_cortex(self):
        session = _session(persona_mode="tiny_nova", response_mode="tiny")
        result = bridge_nova_face_to_cortex_and_jarvis(
            session,
            {},
            "Should I rest or keep working?",
            companion_turn=True,
            surface_profile=TINY_PROFILE,
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.face.face_id, "tiny_nova")
        self.assertIsNotNone(result.cortex_session)
        self.assertIn("jarvis.reasoning", result.jarvis_binding.get("active_cognitive_runtimes", []))
        self.assertEqual(session.metadata["jarvis_core_binding"]["surface_identity"], "tiny_nova")
        self.assertEqual(
            session.metadata["nova_face_bridge"]["pipeline"],
            ["nova_face", "nova_cortex", "jarvis_core"],
        )

    def test_jarvis_retains_authority(self):
        face = resolve_nova_face(
            persona_mode="tiny_nova",
            response_mode="tiny",
            companion_turn=True,
            surface_profile=TINY_PROFILE,
        )
        binding = build_jarvis_core_binding(face, None)
        self.assertEqual(binding["routing_authority"], "jarvis")
        self.assertEqual(binding["state_authority"], "jarvis")
        self.assertEqual(binding["surface_identity"], "tiny_nova")


if __name__ == "__main__":
    unittest.main()
