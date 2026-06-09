"""Tests for Governance IR builder."""

import unittest

from src.governance_ir import (
    GOVERNANCE_IR_VERSION,
    GovernanceIRValidationError,
    build_governance_ir,
)
from src.jarvis_detachment_guard import build_bridge_attestation
from pathlib import Path
import tempfile


def _sample_bridge_result(*, packet_type: str = "deliberation_request") -> dict:
    runtime_dir = Path(tempfile.mkdtemp(prefix="gov-ir-test-"))
    payload = {
        "question": "What is the current state?",
        "intent": "general_qa",
        "execution_intent": "observe",
        "trace_id": "trace-gov-ir-1",
        "bridge_attestation": build_bridge_attestation(
            ingress="unit_test",
            surface="governance_ir_test",
            source_id="trace-gov-ir-1",
            route="tests.governance_ir",
            intent="observe",
            runtime_context="live_runtime",
            packet_type=packet_type,
            runtime_dir=runtime_dir,
        ),
    }
    normalized = {
        "source": "ugr_runtime",
        "type": packet_type,
        "payload": payload,
    }
    governance = {
        "source": "ugr_runtime",
        "packet_type": packet_type,
        "execution_intent": "observe",
        "runtime_context": "live_runtime",
        "effectful": False,
        "requires_approval": False,
        "invariants": [
            "packet_shape_complete",
            "payload_present",
            "runtime_context_explicit",
            "governance_packet_emitted",
            "structured_trace_emitted",
            "aris_runtime_boundary_enforced",
            "aris_does_not_self_apply",
            "governed_llm_proposal_required",
        ],
        "packet_fingerprint": "fp-test-001",
    }
    return {
        "bridge_id": "aais.cognitive_bridge",
        "decision": "ALLOW",
        "normalized_input": normalized,
        "governance_packet": governance,
    }


class TestGovernanceIR(unittest.TestCase):
    def test_build_governance_ir_emits_v1_schema(self):
        ir = build_governance_ir(bridge_result=_sample_bridge_result())
        self.assertEqual(ir["ir_version"], GOVERNANCE_IR_VERSION)
        self.assertTrue(ir.get("ir_fingerprint"))
        self.assertIn("authority_envelope", ir)
        self.assertIn("invariant_set", ir)
        self.assertIn("execution_context", ir)

    def test_build_governance_ir_is_deterministic_for_same_inputs(self):
        bridge = _sample_bridge_result()
        first = build_governance_ir(bridge_result=bridge)
        second = build_governance_ir(bridge_result=bridge)
        self.assertEqual(first["ir_fingerprint"], second["ir_fingerprint"])
        self.assertEqual(first["clock_tick_id"], second["clock_tick_id"])

    def test_build_governance_ir_classifies_hard_and_conditional(self):
        bridge = _sample_bridge_result()
        bridge["governance_packet"]["effectful"] = True
        bridge["governance_packet"]["requires_approval"] = True
        bridge["governance_packet"]["invariants"].extend(
            [
                "effectful_execution_is_governed",
                "approval_state_declared",
                "verification_alignment_required",
            ]
        )
        ir = build_governance_ir(bridge_result=bridge)
        hard = set(ir["invariant_set"]["hard"])
        conditional = {item["name"] for item in ir["invariant_set"]["conditional"]}
        self.assertIn("packet_shape_complete", hard)
        self.assertIn("effectful_execution_is_governed", conditional)
        self.assertIn("approval_state_declared", conditional)

    def test_build_governance_ir_rejects_missing_bridge_fields(self):
        with self.assertRaises(GovernanceIRValidationError):
            build_governance_ir(bridge_result={"bridge_id": "incomplete"})


if __name__ == "__main__":
    unittest.main()
