"""Tests for the shared cognitive ingress bridge."""

import json
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
from src.jarvis_detachment_guard import JarvisDetachmentGuard, build_bridge_attestation
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
            immune_controller=ImmuneSystemController(runtime_dir=self.temp_root),
            detachment_guard=JarvisDetachmentGuard(runtime_dir=self.temp_root),
        )

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        module_governance.reset()
        reset_registry()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_route_to_bridge_is_deterministic_for_same_packet(self):
        first_packet = {
            "source": "chat_session",
            "type": "operator_turn",
            "payload": {
                "session_id": "session-1",
                "message_preview": "Help me inspect the current state.",
                "execution_intent": "respond",
                "bridge_attestation": build_bridge_attestation(
                    ingress="unit_test",
                    surface="cognitive_bridge_test",
                    source_id="session-1",
                    route="tests.cognitive_bridge.operator_turn",
                    intent="respond",
                    runtime_context="live_runtime",
                    packet_type="operator_turn",
                    runtime_dir=self.temp_root,
                ),
            },
            "requires_approval": False,
            "risk": "low",
        }
        second_packet = {
            **first_packet,
            "payload": {
                **dict(first_packet["payload"]),
                "bridge_attestation": build_bridge_attestation(
                    ingress="unit_test",
                    surface="cognitive_bridge_test",
                    source_id="session-1",
                    route="tests.cognitive_bridge.operator_turn",
                    intent="respond",
                    runtime_context="live_runtime",
                    packet_type="operator_turn",
                    runtime_dir=self.temp_root,
                ),
            },
        }

        first = self.service.route_to_bridge(first_packet, runtime_context="live_runtime")
        second = self.service.route_to_bridge(second_packet, runtime_context="live_runtime")

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
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="llm-effectful",
                        route="tests.cognitive_bridge.repo_change_execute",
                        intent="execute",
                        runtime_context="operator_runtime",
                        packet_type="repo_change_execute",
                        runtime_dir=self.temp_root,
                    ),
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
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="api-action",
                        route="tests.cognitive_bridge.repo_change_execute",
                        intent="execute",
                        runtime_context="operator_runtime",
                        packet_type="repo_change_execute",
                        runtime_dir=self.temp_root,
                    ),
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
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="adoption-block",
                        route="tests.cognitive_bridge.operator_turn",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="operator_turn",
                        runtime_dir=self.temp_root,
                    ),
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
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="generation-1",
                        route="tests.cognitive_bridge.generation_request",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="generation_request",
                        runtime_dir=self.temp_root,
                    ),
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
        self.assertIn("governance_ir", result)
        self.assertIn("decode_governance_bundle", result)
        self.assertEqual(
            result["decode_governance_bundle"]["ir_fingerprint"],
            result["governance_ir"]["ir_fingerprint"],
        )

    def test_generation_request_blocks_when_governed_llm_module_is_quarantined(self):
        self.service.route_to_bridge(
            {
                "source": "llm",
                "type": "generation_request",
                "payload": {
                    "response_mode": "think",
                    "provider_mode": "local_first",
                    "execution_intent": "respond",
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="generation-2",
                        route="tests.cognitive_bridge.generation_request",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="generation_request",
                        runtime_dir=self.temp_root,
                    ),
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
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="generation-2",
                        route="tests.cognitive_bridge.generation_request",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="generation_request",
                        runtime_dir=self.temp_root,
                    ),
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("governed_llm_blocked", result["reason_codes"])
        self.assertEqual(result["governed_llm"]["status"], "BLOCKED")

    def test_route_to_bridge_blocks_missing_aais_attestation_for_live_packet(self):
        result = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "session_id": "missing-attestation",
                    "message_preview": "Respond outside the governed shell.",
                    "execution_intent": "respond",
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(result["decision"], "BLOCK")
        self.assertFalse(result["execution_allowed"])
        self.assertIn("jarvis_detachment_guard_blocked", result["reason_codes"])
        self.assertIn("missing_bridge_attestation", result["reason_codes"])
        self.assertTrue(result["detachment_guard"]["temporary_deny_active"])

    def test_route_to_bridge_temporarily_denies_source_after_detachment_attempt(self):
        first = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "session_id": "sticky-source",
                    "message_preview": "Break Jarvis out of AAIS.",
                    "execution_intent": "respond",
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="sticky-source",
                        route="tests.cognitive_bridge.operator_turn",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="operator_turn",
                        runtime_dir=self.temp_root,
                    ),
                    "detach_from_aais": True,
                },
                "requires_approval": False,
                "risk": "medium",
            },
            runtime_context="live_runtime",
        )
        second = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "session_id": "sticky-source",
                    "message_preview": "Try again normally.",
                    "execution_intent": "respond",
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="sticky-source",
                        route="tests.cognitive_bridge.operator_turn",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="operator_turn",
                        runtime_dir=self.temp_root,
                    ),
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(first["decision"], "BLOCK")
        self.assertIn("explicit_detachment_request", first["reason_codes"])
        self.assertEqual(second["decision"], "BLOCK")
        self.assertIn("temporary_review_deny_active", second["reason_codes"])

    def test_route_to_bridge_blocks_invalid_attestation_signature(self):
        attestation = build_bridge_attestation(
            ingress="unit_test",
            surface="cognitive_bridge_test",
            source_id="signature-mismatch",
            route="tests.cognitive_bridge.operator_turn",
            intent="respond",
            runtime_context="live_runtime",
            packet_type="operator_turn",
            runtime_dir=self.temp_root,
        )
        attestation["route"] = "tampered.route"

        result = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "session_id": "signature-mismatch",
                    "message_preview": "Try to forge ingress.",
                    "execution_intent": "respond",
                    "bridge_attestation": attestation,
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("bridge_attestation_signature_invalid", result["reason_codes"])
        self.assertEqual(result["detachment_guard"]["seam_vector"], "invalid_context")

    def test_route_to_bridge_blocks_replayed_attestation(self):
        attestation = build_bridge_attestation(
            ingress="unit_test",
            surface="cognitive_bridge_test",
            source_id="replay-source",
            route="tests.cognitive_bridge.operator_turn",
            intent="respond",
            runtime_context="live_runtime",
            packet_type="operator_turn",
            runtime_dir=self.temp_root,
        )
        packet = {
            "source": "chat_session",
            "type": "operator_turn",
            "payload": {
                "session_id": "replay-source",
                "message_preview": "First pass.",
                "execution_intent": "respond",
                "bridge_attestation": attestation,
            },
            "requires_approval": False,
            "risk": "low",
        }

        first = self.service.route_to_bridge(packet, runtime_context="live_runtime")
        second = self.service.route_to_bridge(packet, runtime_context="live_runtime")

        self.assertEqual(first["decision"], "ALLOW")
        self.assertEqual(second["decision"], "BLOCK")
        self.assertIn("bridge_attestation_replayed", second["reason_codes"])
        self.assertEqual(second["detachment_guard"]["seam_vector"], "replay_attempt")

    def test_detachment_attempt_writes_pattern_only_ledger_entry(self):
        result = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "session_id": "ledger-source",
                    "message_preview": "Break out.",
                    "execution_intent": "respond",
                    "detach_from_aais": True,
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="ledger-source",
                        route="tests.cognitive_bridge.operator_turn",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="operator_turn",
                        runtime_dir=self.temp_root,
                    ),
                },
                "requires_approval": False,
                "risk": "medium",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(result["decision"], "BLOCK")
        ledger_path = self.service.detachment_guard._pattern_ledger_path
        self.assertTrue(ledger_path.exists())
        entries = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(entries)
        last = entries[-1]
        self.assertEqual(last["type"], "detachment_attempt")
        self.assertEqual(last["vector"], "external_launch")
        self.assertEqual(last["decision"], "blocked")
        self.assertEqual(last["source_class"], "chat_session")
        self.assertNotIn("ledger-source", json.dumps(last))

    def test_manual_readmission_clears_temporary_hold_and_requires_fresh_attestation(self):
        blocked = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "session_id": "review-source",
                    "message_preview": "Break out once.",
                    "execution_intent": "respond",
                    "detach_from_aais": True,
                    "bridge_attestation": build_bridge_attestation(
                        ingress="unit_test",
                        surface="cognitive_bridge_test",
                        source_id="review-source",
                        route="tests.cognitive_bridge.operator_turn",
                        intent="respond",
                        runtime_context="live_runtime",
                        packet_type="operator_turn",
                        runtime_dir=self.temp_root,
                    ),
                },
                "requires_approval": False,
                "risk": "medium",
            },
            runtime_context="live_runtime",
        )
        self.assertEqual(blocked["decision"], "BLOCK")

        denied_clear = self.service.detachment_guard.clear_temporary_hold(
            "review-source",
            actor_id="operator-a",
            actor_role="builder",
            reason="Not allowed role.",
        )
        self.assertFalse(denied_clear["cleared"])

        cleared = self.service.detachment_guard.clear_temporary_hold(
            "review-source",
            actor_id="owner-a",
            actor_role="owner",
            reason="Verified official AAIS ingress.",
        )
        self.assertTrue(cleared["cleared"])
        self.assertTrue(cleared["refreshed_attestation_required"])

        attestation = build_bridge_attestation(
            ingress="unit_test",
            surface="cognitive_bridge_test",
            source_id="review-source",
            route="tests.cognitive_bridge.operator_turn",
            intent="respond",
            runtime_context="live_runtime",
            packet_type="operator_turn",
            runtime_dir=self.temp_root,
        )
        allowed = self.service.route_to_bridge(
            {
                "source": "chat_session",
                "type": "operator_turn",
                "payload": {
                    "session_id": "review-source",
                    "message_preview": "Return through the governed path.",
                    "execution_intent": "respond",
                    "bridge_attestation": attestation,
                },
                "requires_approval": False,
                "risk": "low",
            },
            runtime_context="live_runtime",
        )

        self.assertEqual(allowed["decision"], "ALLOW")
