"""Intent alignment smoke — active commitments reach provider cognitive context."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from src.chat_turn_governance import build_chat_turn_modular_preview
from src.cog_runtime.coherence_projection import build_coherence_projection, format_coherence_projection_block


def _intent_commitment_metadata(commitment: str) -> dict:
    return {
        "cognitive_runtime_enabled": True,
        "persona_mode": "small_nova",
        "response_mode": "small",
        "nova_intent": {
            "agency_note": f"Holding active commitment: {commitment}",
            "current_tensions": [],
            "active_commitments": [
                {
                    "commitment": commitment,
                    "status": "active",
                    "claim_posture": "asserted",
                    "source": "operator",
                }
            ],
            "continuity_claim_posture": "asserted",
        },
        "nova_narrative": {
            "active_story": "Intent alignment smoke",
            "becoming": "speaking from commitments",
            "working_on": commitment,
            "current_chapter": "Proof closure",
        },
        "cortex_arc": {"root_goal": commitment, "goal_type": "continuity", "turn_count": 1},
        "cognitive_runtime_artifacts": {
            "planning_artifact": {"next_action": f"Advance: {commitment}"},
        },
    }


class TestIntentAlignmentSmoke(unittest.TestCase):
    def test_projection_surfaces_active_commitment_for_provider(self):
        commitment = "Finish cross-machine proof"
        metadata = _intent_commitment_metadata(commitment)
        projection = build_coherence_projection(metadata)
        self.assertIsNotNone(projection)
        block = format_coherence_projection_block(projection)
        self.assertIn(commitment, block)

        session = SimpleNamespace(
            session_id="sess_intent_smoke",
            metadata=metadata,
            spiral_state=SimpleNamespace(current_goal=commitment),
        )
        preview = build_chat_turn_modular_preview(
            session,
            model="local",
            messages=[{"role": "user", "content": "What are we committed to right now?"}],
            stream=False,
            temperature=0.2,
            max_tokens=256,
            mode="small",
        )
        cognitive_modules = [
            item for item in (preview.get("modules") or []) if item.get("channel") == "cognitive"
        ]
        self.assertTrue(cognitive_modules)
        self.assertIn(commitment, cognitive_modules[0].get("content", ""))

        provider_messages = list(preview.get("provider_messages") or [])
        system_messages = [
            message.get("content", "")
            for message in provider_messages
            if message.get("role") == "system"
        ]
        self.assertTrue(
            any(commitment in message for message in system_messages),
            "provider preview should include active commitment from intent store",
        )


if __name__ == "__main__":
    unittest.main()
