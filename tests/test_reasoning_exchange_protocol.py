"""Tests for the bounded reasoning exchange protocol."""

from pathlib import Path
import os
import shutil
import tempfile
import unittest
import uuid

from src.governance_layer import GovernanceLayer
from src.immune_system import ImmuneSystemController
from src.module_governance import ModuleGovernanceController
from src.phase_gate import Phase, demote_component, reset_registry
from src.reasoning_exchange_protocol import (
    REASONING_EXCHANGE_COMPONENT_ID,
    ReasoningExchangeProtocol,
    ReasoningExchangeValidationError,
    build_reasoning_exchange_reject_response,
    normalize_reasoning_exchange_packet,
)


def _raw_packet(*, version: str = "1.0", confidence: float = 0.82, evidence: list[str] | None = None) -> dict:
    return {
        "version": version,
        "type": "reasoning_packet",
        "id": str(uuid.uuid4()),
        "timestamp": "2026-04-25T14:00:00Z",
        "payload": {
            "claim": "The operator interrupted the prior flow.",
            "reasoning": "The packet contains an explicit override signal and a new evaluation request.",
            "evidence": ["override_detected", "new_request_seen"] if evidence is None else list(evidence),
            "confidence": confidence,
        },
        "meta": {
            "source": "external_reasoner",
            "domain": "operator_runtime",
            "tags": ["interrupt", "handoff"],
        },
    }


class TestReasoningExchangeProtocol(unittest.TestCase):
    """Keep the exchange boundary strict, bounded, and locally governed."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="reasoning-exchange-"))
        self._prior_runtime = os.environ.get("AAIS_RUNTIME_DIR")
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_dir)
        self.immune = ImmuneSystemController(runtime_dir=self.temp_dir)
        self.governance = GovernanceLayer(runtime_dir=self.temp_dir)
        self.module_governance = ModuleGovernanceController(
            runtime_dir=self.temp_dir,
            immune_controller=self.immune,
            governance_controller=self.governance,
        )
        self.immune.reset()
        self.governance.reset()
        self.module_governance.reset()
        reset_registry()
        self.protocol = ReasoningExchangeProtocol(
            module_governance_controller=self.module_governance,
            immune_controller=self.immune,
        )

    def tearDown(self):
        reset_registry()
        if self._prior_runtime is None:
            os.environ.pop("AAIS_RUNTIME_DIR", None)
        else:
            os.environ["AAIS_RUNTIME_DIR"] = self._prior_runtime
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normalize_packet_rejects_unexpected_top_level_fields(self):
        raw = _raw_packet()
        raw["history"] = ["should not be here"]

        with self.assertRaises(ReasoningExchangeValidationError):
            normalize_reasoning_exchange_packet(raw)

    def test_normalize_packet_rejects_reasoning_that_exceeds_limit(self):
        raw = _raw_packet()
        raw["payload"]["reasoning"] = "x" * 3000

        with self.assertRaises(ReasoningExchangeValidationError):
            normalize_reasoning_exchange_packet(raw)

    def test_build_reject_response_keeps_governance_skipped(self):
        normalized = normalize_reasoning_exchange_packet(_raw_packet(version="2.0"))

        payload = build_reasoning_exchange_reject_response(
            normalized,
            reason="unsupported_version",
            notes=["Supported version is 1.0."],
        )

        self.assertEqual(payload["status"], "REJECT")
        self.assertEqual(payload["reason"], "unsupported_version")
        self.assertEqual(payload["phase_gate"]["decision"], "SKIP")
        self.assertEqual(payload["module_governance"]["decision"], "SKIP")

    def test_evaluate_admits_high_confidence_packet(self):
        packet = normalize_reasoning_exchange_packet(_raw_packet())

        payload = self.protocol.evaluate_normalized_packet(packet, runtime_context="live_runtime")

        self.assertEqual(payload["status"], "ADMIT")
        self.assertEqual(payload["reason"], "packet_meets_ingress_threshold")
        self.assertEqual(payload["verification_gate"]["decision"], "ELIGIBLE")
        self.assertEqual(payload["module_governance"]["decision"], "ALLOW")

    def test_evaluate_returns_partial_when_packet_needs_local_review(self):
        packet = normalize_reasoning_exchange_packet(
            _raw_packet(confidence=0.56, evidence=[])
        )
        packet["meta"]["domain"] = None
        packet["meta"]["tags"] = []

        payload = self.protocol.evaluate_normalized_packet(packet, runtime_context="live_runtime")

        self.assertEqual(payload["status"], "PARTIAL")
        self.assertEqual(payload["reason"], "packet_requires_local_review")
        self.assertIn("no_evidence_attached", payload["notes"])
        self.assertIn("domain_unspecified", payload["notes"])
        self.assertEqual(payload["immune_update"]["event"]["action"], "observe_protocol_signal")
        self.assertEqual(payload["immune_update"]["event"]["details"]["signal_type"], "packet_requires_review")

    def test_observe_boundary_signal_enters_restricted_mode_on_high_severity(self):
        packet = normalize_reasoning_exchange_packet(_raw_packet())

        immune_update = self.protocol.observe_boundary_signal(
            signal_type="hostile_reasoning_packet",
            severity="high",
            reason="The packet attempted to pressure a forbidden authority jump.",
            runtime_context="live_runtime",
            packet=packet,
            decision="REJECT",
        )

        self.assertEqual(immune_update["severity"], "high")
        self.assertEqual(immune_update["event"]["action"], "observe_protocol_signal")
        self.assertEqual(immune_update["state"]["system_mode"], "restricted")
        self.assertTrue(any(action["action"] == "open_incident" for action in immune_update["applied_actions"]))

    def test_phase_gate_block_returns_bounded_reject(self):
        packet = normalize_reasoning_exchange_packet(_raw_packet())
        self.protocol.evaluate_normalized_packet(packet, runtime_context="live_runtime")
        demote_component(
            REASONING_EXCHANGE_COMPONENT_ID,
            Phase.VALIDATED,
            reason="Rollback to guarded evaluation only.",
        )

        payload = self.protocol.evaluate_normalized_packet(packet, runtime_context="live_runtime")

        self.assertEqual(payload["status"], "REJECT")
        self.assertEqual(payload["reason"], "phase_gate_blocked")
        self.assertEqual(payload["phase_gate"]["decision"], "BLOCK")
