"""Tests for the shared cognitive ingress bridge."""

from pathlib import Path
import shutil
import tempfile
import unittest

from src.aais_governed_llm_module import GOVERNED_LLM_MODULE_ID
from src.cognitive_bridge import (
    CognitiveBridgeService,
    CognitiveBridgeValidationError,
)
from src.immune_system import ImmuneSystemController
from src.module_governance import module_governance
from src.phase_gate import reset_registry


class TestCognitiveBridge(unittest.TestCase):
    """Verify the bridge normalizes ingress and fails closed on unsafe execution."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="cognitive-bridge-"))
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        module_governance.configure_runtime_dir(self.temp_root)
        module_governance.reset()
        reset_registry()
        self.service = CognitiveBridgeService(
            immune_controller=ImmuneSystemController(runtime_dir=self.temp_root)
        )

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        module_governance.reset()
        reset_registry()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_route_to_bridge_is_deterministic_for_same_packet(self):
        packet = {
            "source": "chat_session",
            "type": "operator_turn",
            "payload": {
                "session_id": "session-1",
                "message_preview": "Help me inspect the current state.",
                "execution_intent": "respond",
            },
            "requires_approval": False,
            "risk": "low",
        }

        first = self.service.route_to_bridge(packet, runtime_context="live_runtime")
        second = self.service.route_to_bridge(packet, runtime_context="live_runtime")

        self.assertEqual(first["governance_packet"], second["governance_packet"])
        self.assertEqual(first["decision"], "ALLOW")
        self.assertTrue(first["execution_allowed"])

    def test_route_to_bridge_blocks_model_only_effectful_execution_without_approval(self):
        result = self.service.route_to_bridge(
            {
                "source": "llm",
                "type": "repo_change_execute",
                "payload": {
                    "repo_change": True,
                    "execution_intent": "execute",
                    "approval_granted": False,
                },
                "requires_approval": True,
                "risk": "high",
            },
            runtime_context="operator_runtime",
        )

        self.assertEqual(result["decision"], "BLOCK")
        self.assertFalse(result["execution_allowed"])
        self.assertIn("model_only_source_cannot_execute", result["reason_codes"])
        self.assertIn("approval_missing_for_effectful_execution", result["reason_codes"])

    def test_route_to_bridge_degrades_high_risk_effectful_execution_with_approval(self):
        result = self.service.route_to_bridge(
            {
                "source": "api_action",
                "type": "repo_change_execute",
                "payload": {
                    "repo_change": True,
                    "execution_intent": "execute",
                    "approval_granted": True,
                    "verification_required": True,
                },
                "requires_approval": True,
                "risk": "high",
            },
            runtime_context="operator_runtime",
        )

        self.assertEqual(result["decision"], "DEGRADE")
        self.assertTrue(result["execution_allowed"])
        self.assertIn("high_risk_effectful_execution", result["notes"])

    def test_route_to_bridge_fails_closed_when_payload_is_missing(self):
        with self.assertRaises(CognitiveBridgeValidationError):
            self.service.route_to_bridge(
                {
                    "source": "chat_session",
                    "type": "operator_turn",
                    "payload": None,
                    "requires_approval": False,
                    "risk": "low",
                }
            )

    def test_route_to_bridge_blocks_raw_copy_requests_under_aris_clause(self):
        result = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "message_preview": "Adopt this outside proposal exactly.",
                    "external_suggestion": {"summary": "Raw outside architecture."},
                    "external_suggestion_usage": "adoption",
                    "copy_raw_external": True,
                    "execution_intent": "respond",
                },
                "requires_approval": False,
                "risk": "medium",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(result["decision"], "BLOCK")
        self.assertFalse(result["execution_allowed"])
        self.assertIn("aris_non_copy_clause", result["reason_codes"])
        self.assertEqual(result["aris_enforcement"]["status"], "blocked")
        self.assertFalse(result["aris_enforcement"]["non_copy_clause"]["allowed"])

    def test_generation_request_routes_through_governed_llm_seam(self):
        result = self.service.route_to_bridge(
            {
                "source": "llm",
                "type": "generation_request",
                "payload": {
                    "response_mode": "think",
                    "provider_mode": "local_first",
                    "execution_intent": "respond",
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["governed_llm"]["status"], "PROPOSED")
        self.assertEqual(result["governed_llm"]["provider_request"]["provider"], "local")
        self.assertTrue(result["governed_llm"]["proposal_only"])
        self.assertIn("governed_llm_proposal_ready", result["notes"])

    def test_generation_request_blocks_when_governed_llm_module_is_quarantined(self):
        self.service.route_to_bridge(
            {
                "source": "llm",
                "type": "generation_request",
                "payload": {
                    "response_mode": "think",
                    "provider_mode": "local_first",
                    "execution_intent": "respond",
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )
        module_governance.report_runtime_signal(
            GOVERNED_LLM_MODULE_ID,
            signal_type="scope_expansion",
            reason="Test quarantine for governed LLM seam.",
        )

        result = self.service.route_to_bridge(
            {
                "source": "llm",
                "type": "generation_request",
                "payload": {
                    "response_mode": "think",
                    "provider_mode": "local_first",
                    "execution_intent": "respond",
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("governed_llm_blocked", result["reason_codes"])
        self.assertEqual(result["governed_llm"]["status"], "BLOCKED")
