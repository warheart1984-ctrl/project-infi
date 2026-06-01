"""Tests for chat-turn UL substrate and CISIV-staged Project Infi admission."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.chat_turn_governance import (
    CHAT_TURN_SURFACE,
    attach_modular_preview_to_response_trace,
    build_chat_runtime_ul_envelope,
    build_chat_turn_modular_preview,
    finalize_chat_turn_admission,
    infer_chat_turn_cisiv_stage,
    prepare_chat_turn_modular_package,
    provider_messages_from_preview,
    store_chat_turn_modular_preview,
    wrap_chat_runtime_payload,
)
from src.cisiv import CISIV_STAGE_SEQUENCE


class TestChatTurnGovernance(unittest.TestCase):
    def test_infer_chat_turn_cisiv_stage(self):
        self.assertEqual(infer_chat_turn_cisiv_stage(phase="ingress"), "concept")
        self.assertEqual(infer_chat_turn_cisiv_stage(phase="bridge"), "identity")
        self.assertEqual(infer_chat_turn_cisiv_stage(phase="gather"), "structure")
        self.assertEqual(infer_chat_turn_cisiv_stage(phase="generate"), "implementation")
        self.assertEqual(infer_chat_turn_cisiv_stage(phase="admit"), "verification")
        self.assertEqual(infer_chat_turn_cisiv_stage(phase="unknown"), "implementation")

    def test_wrap_chat_runtime_payload_attaches_ul_substrate(self):
        wrapped = wrap_chat_runtime_payload(
            {
                "session_id": "sess_test",
                "turn_count": 1,
                "cisiv_stage": "structure",
                "cisiv_stage_sequence": list(CISIV_STAGE_SEQUENCE),
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("ul_trace", wrapped)

    def test_build_chat_runtime_ul_envelope_includes_bridge_and_pipeline(self):
        envelope = build_chat_runtime_ul_envelope(
            {
                "cognitive_bridge": {
                    "bridge_id": "aais.cognitive_bridge",
                    "decision": "ALLOW",
                    "status": "ready",
                    "execution_allowed": True,
                    "risk": "low",
                    "summary": "cleared",
                },
                "response_trace": {
                    "governed_pipeline": {
                        "protocol_id": "aais.governed_direct_pipeline",
                        "pipeline_id": "gdp_test",
                        "active_lane": "direct_cognitive",
                        "traffic_class": "core_cognition",
                        "response_mode": "fast",
                        "summary": "direct lane",
                    }
                },
            }
        )
        self.assertGreaterEqual(envelope["ul_trace"]["count"], 2)
        self.assertIn("protocol_trace", envelope["ul_trace"]["sections"])
        self.assertIn("mission_context", envelope["ul_trace"]["sections"])

    @patch("src.chat_turn_governance.build_and_store_chat_turn_preview")
    def test_prepare_chat_turn_modular_package(self, mock_store):
        preview = {
            "provider_messages": [{"role": "user", "content": "hello"}],
            "ul_trace": {"count": 2, "sections": ["provider_payload", "guardrail_state"]},
        }
        mock_store.return_value = preview
        session = SimpleNamespace(session_id="sess_pkg", metadata={})
        package = prepare_chat_turn_modular_package(
            session,
            protocol_messages=[{"role": "user", "content": "hello"}],
            model="local",
            stream=False,
            temperature=0.2,
            max_tokens=128,
            mode="fast",
        )
        self.assertEqual(package["preview"], preview)
        self.assertEqual(len(package["provider_messages"]), 1)
        mock_store.assert_called_once()

    def test_provider_messages_from_preview(self):
        from src.jarvis_protocol import JarvisMessage

        preview = {
            "provider_messages": [
                {"role": "user", "content": "hello"},
                JarvisMessage(role="assistant", content="hi"),
            ]
        }
        messages = provider_messages_from_preview(preview)
        self.assertEqual(len(messages), 2)
        self.assertIsInstance(messages[0], JarvisMessage)
        self.assertIsInstance(messages[1], JarvisMessage)

    def test_attach_modular_preview_to_response_trace(self):
        trace = {"contract": "chat"}
        preview = {
            "context_modules": ["identity"],
            "pipeline_mode": "fast",
            "doctrine_summary": "stable",
            "guardrail_evaluation": {"status": "ok"},
            "ul_trace": {"count": 2, "sections": ["provider_payload", "guardrail_state"]},
        }
        attach_modular_preview_to_response_trace(trace, preview)
        mirrored = trace["modular_preview"]
        self.assertEqual(mirrored["context_modules"], ["identity"])
        self.assertIn("provider_payload", mirrored["ul_trace"]["sections"])

    @patch("src.jarvis_modular.build_modular_provider_preview")
    def test_build_chat_turn_modular_preview_passes_cisiv_metadata(self, mock_preview):
        mock_preview.return_value = {"ul_trace": {"count": 1, "sections": ["identity"]}}
        session = SimpleNamespace(
            session_id="sess_preview",
            metadata={"response_trace": {"contract": "chat"}},
            spiral_state=SimpleNamespace(current_goal="Verify UL wiring"),
        )
        build_chat_turn_modular_preview(
            session,
            model="local",
            messages=[{"role": "user", "content": "hello"}],
            stream=False,
            temperature=0.2,
            max_tokens=128,
            mode="fast",
        )
        metadata = mock_preview.call_args.kwargs["metadata"]
        self.assertEqual(metadata["cisiv_stage"], "implementation")
        self.assertEqual(metadata["session_id"], "sess_preview")

    def test_store_chat_turn_modular_preview(self):
        session = SimpleNamespace(session_id="sess_store", metadata={})
        preview = {"ul_trace": {"count": 2, "sections": ["runtime_context", "identity"]}}
        store_chat_turn_modular_preview(session, preview)
        self.assertEqual(session.metadata["modular_preview"], preview)
        self.assertEqual(session.metadata["ul_snapshot"]["count"], 2)
        self.assertEqual(session.metadata["cisiv_stage"], "implementation")

    @patch("src.chat_turn_governance._chat_turn_law")
    def test_finalize_chat_turn_admission_allows_successful_cycle(self, mock_chat_turn_law):
        session = SimpleNamespace(
            session_id="sess_admit",
            metadata={
                "persona_mode": "jarvis",
                "response_mode": "fast",
                "cognitive_bridge": {"decision": "ALLOW", "status": "ready"},
            },
        )
        mock_law = mock_chat_turn_law.return_value
        mock_law.require_contract.return_value = (
            {"request_scope": {"surface": CHAT_TURN_SURFACE}},
            {"count": 1, "sections": ["identity"]},
            {},
        )
        mock_law.finalize_runtime_action.return_value = (
            {"governed_cycle": {"status": "success"}, "project_infi_layers": {"outcome": {"detail": "ok"}}},
            {"id": "evt_1"},
        )
        text, blocked = finalize_chat_turn_admission(
            session,
            user_message="Summarize UL",
            response_text="UL carries law and structure.",
        )
        self.assertEqual(text, "UL carries law and structure.")
        self.assertIsNone(blocked)
        self.assertEqual(session.metadata["cisiv_stage"], "verification")
        mock_law.require_contract.assert_called_once()
        call_kwargs = mock_law.require_contract.call_args.kwargs
        self.assertEqual(call_kwargs["surface"], CHAT_TURN_SURFACE)
        self.assertEqual(call_kwargs["cisiv_stage"], "verification")

    @patch("src.chat_turn_governance._chat_turn_law")
    def test_finalize_chat_turn_admission_blocks_failed_cycle(self, mock_chat_turn_law):
        session = SimpleNamespace(
            session_id="sess_block",
            metadata={
                "persona_mode": "jarvis",
                "response_mode": "fast",
                "cognitive_bridge": {"decision": "ALLOW", "status": "ready"},
                "modular_preview": {"ul_trace": {"count": 1, "sections": ["identity"]}},
            },
        )
        response_trace = {"contract": "chat"}
        mock_law = mock_chat_turn_law.return_value
        mock_law.require_contract.return_value = (
            {"request_scope": {"surface": CHAT_TURN_SURFACE}},
            {"count": 1, "sections": ["identity"]},
            {},
        )
        mock_law.finalize_runtime_action.return_value = (
            {
                "governed_cycle": {"status": "rejected_no_admission", "truthful": False},
                "project_infi_layers": {"outcome": {"detail": "Admission rejected for test."}},
            },
            {"id": "evt_block"},
        )
        text, blocked = finalize_chat_turn_admission(
            session,
            user_message="Unsafe reply",
            response_text="Unsafe reply",
            response_trace=response_trace,
        )
        self.assertEqual(text, "Admission rejected for test.")
        self.assertEqual(blocked["status_code"], 409)
        self.assertEqual(blocked["law_enforcement"]["governed_cycle"]["status"], "rejected_no_admission")
        self.assertTrue(response_trace["chat_turn_admission"]["blocked"])
        self.assertEqual(response_trace["chat_turn_admission"]["cisiv_stage"], "verification")


if __name__ == "__main__":
    unittest.main()
