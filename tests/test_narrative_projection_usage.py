"""Prove companion chat turns pass coherence projection into provider context (INV-3 LLM usage)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import src.api as api
from src.chat_turn_governance import build_chat_turn_modular_preview
from src.conversation_memory import conversation_memory
from src.phase_gate import reset_registry


def _companion_cognitive_metadata(**overrides) -> dict:
    payload = {
        "cognitive_runtime_enabled": True,
        "persona_mode": "tiny_nova",
        "response_mode": "tiny",
        "nova_intent": {
            "agency_note": "Still committed to proof while pulled toward safety.",
            "current_tensions": [{"poles": ["safety", "exploration"], "pull": "safety"}],
            "active_commitments": [
                {
                    "commitment": "Finish cross-machine proof",
                    "status": "active",
                    "claim_posture": "asserted",
                }
            ],
            "continuity_claim_posture": "asserted",
            "long_horizon_goals": [{"goal": "Persistent continuity", "claim_posture": "asserted"}],
        },
        "nova_narrative": {
            "active_story": "Helping forge Wolf Cog OS",
            "becoming": "improving continuity; pulled toward safety",
            "working_on": "Cross-machine proof",
            "current_chapter": "Nova Cortex Development",
            "open_threads": ["Cross-machine proof", "Unified memory path"],
            "last_growth": "Composed turns integrated into Jarvis",
        },
        "cortex_arc": {"root_goal": "Ship continuity", "goal_type": "continuity", "turn_count": 2},
        "cognitive_runtime_artifacts": {
            "focus_artifact": {"primary_focus": "cross-machine proof"},
            "decision_object": {
                "chosen_option": "Take the safe verified path",
                "rationale": "Governance first.",
            },
            "planning_artifact": {"next_action": "Run wolf reboot fixture"},
        },
    }
    payload.update(overrides)
    return payload


class TestNarrativeProjectionUsage(unittest.TestCase):
    def test_companion_modular_preview_injects_bounded_cognitive_channel(self):
        session = SimpleNamespace(
            session_id="sess_projection_preview",
            metadata=_companion_cognitive_metadata(),
            spiral_state=SimpleNamespace(current_goal="Continue cross-machine proof"),
        )
        preview = build_chat_turn_modular_preview(
            session,
            model="local",
            messages=[{"role": "user", "content": "What should we tackle next on the proof?"}],
            stream=False,
            temperature=0.2,
            max_tokens=256,
            mode="tiny",
        )
        modules = list(preview.get("modules") or [])
        cognitive_modules = [item for item in modules if item.get("channel") == "cognitive"]
        self.assertTrue(cognitive_modules)
        cognitive = cognitive_modules[0]
        self.assertEqual(cognitive.get("source_module"), "NovaCoherenceProjectionModule")
        self.assertTrue(cognitive.get("metadata", {}).get("read_only"))
        content = str(cognitive.get("content") or "")
        self.assertIn("Speak from this cognitive state", content)
        self.assertIn("Finish cross-machine proof", content)
        self.assertIn("Cross-machine proof", content)
        self.assertLessEqual(len(content), 2200)

        provider_messages = list(preview.get("provider_messages") or [])
        system_messages = [
            message.get("content", "")
            for message in provider_messages
            if message.get("role") == "system"
        ]
        self.assertTrue(
            any("Speak from this cognitive state" in message for message in system_messages),
            "provider preview should include coherence projection system context",
        )
        self.assertIn("NovaCoherenceProjectionModule", preview.get("context_modules") or [])

    @patch("src.api.init_ai")
    def test_companion_chat_message_passes_projection_to_generate_chat(self, mock_init_ai):
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "We should keep the cross-machine proof thread moving on the safe verified path."
        )
        mock_init_ai.return_value = (fake_model, object())

        client = api.app.test_client()
        reset_registry()
        conversation_memory.sessions.clear()

        create_response = client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "tiny_nova",
                "response_mode": "tiny",
            },
        )
        self.assertIn(create_response.status_code, {200, 201})
        session_id = create_response.get_json()["session_id"]

        response = client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Where did we leave off on the Wolf proof work?",
                "persona_mode": "tiny_nova",
                "response_mode": "tiny",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        modular_preview = payload.get("modular_preview") or {}
        self.assertIn("NovaCoherenceProjectionModule", modular_preview.get("context_modules") or [])

        preview_modules = list(modular_preview.get("modules") or [])
        cognitive_modules = [item for item in preview_modules if item.get("channel") == "cognitive"]
        self.assertTrue(
            cognitive_modules,
            "companion turn should expose bounded cognitive projection in modular preview",
        )
        self.assertIn("Speak from this cognitive state", cognitive_modules[0].get("content", ""))

        preview_provider_messages = list(modular_preview.get("provider_messages") or [])
        preview_system_messages = [
            message.get("content", "")
            for message in preview_provider_messages
            if message.get("role") == "system"
        ]
        self.assertTrue(
            any("Speak from this cognitive state" in message for message in preview_system_messages),
            "modular provider preview should carry coherence projection for generation",
        )
        fake_model.generate_chat.assert_called_once()


if __name__ == "__main__":
    unittest.main()
