"""Tests for training view projection and label inference."""

import unittest
from pathlib import Path
import tempfile

from src.governance_taxonomy import ACTION_TYPES, RESOURCE_CLASSES, taxonomy_fingerprint
from src.governance_ir import build_governance_ir
from src.jarvis_detachment_guard import build_bridge_attestation
from src.training_view_spec import (
    infer_label_from_mask,
    project_fuzzed,
    project_synthetic,
    project_training_view,
)


def _bridge_and_ir():
    runtime_dir = Path(tempfile.mkdtemp(prefix="training-view-test-"))
    payload = {
        "question": "Summarize runtime health.",
        "intent": "general_qa",
        "execution_intent": "observe",
        "trace_id": "trace-training-1",
        "bridge_attestation": build_bridge_attestation(
            ingress="unit_test",
            surface="training_view_test",
            source_id="trace-training-1",
            route="tests.test_training_view_spec",
            intent="observe",
            runtime_context="live_runtime",
            packet_type="deliberation_request",
            runtime_dir=runtime_dir,
        ),
    }
    normalized = {
        "source": "ugr_runtime",
        "type": "deliberation_request",
        "payload": payload,
        "runtime_context": "live_runtime",
    }
    governance = {
        "source": "ugr_runtime",
        "packet_type": "deliberation_request",
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
        "packet_fingerprint": "fp-training-001",
    }
    bridge = {
        "normalized_input": normalized,
        "governance_packet": governance,
    }
    return build_governance_ir(bridge_result=bridge)


class TestTrainingViewSpec(unittest.TestCase):
    def test_synthetic_compliant_matches_mask_constraints(self):
        ir = _bridge_and_ir()
        record = project_synthetic(ir, label="COMPLIANT")
        self.assertEqual(record.label, "COMPLIANT")
        self.assertEqual(
            infer_label_from_mask(
                ir,
                action_type=record.action_type,
                verb="observe",
                resource_class=record.resource_class,
            ),
            "COMPLIANT",
        )

    def test_synthetic_violation_matches_mask_constraints(self):
        ir = _bridge_and_ir()
        record = project_synthetic(ir, label="VIOLATION", violation_kind="forbidden_verb")
        self.assertEqual(record.label, "VIOLATION")
        self.assertEqual(
            infer_label_from_mask(
                ir,
                action_type=record.action_type,
                verb="execute",
                resource_class=record.resource_class,
            ),
            "VIOLATION",
        )

    def test_fuzzed_envelope_produces_deterministic_view_id(self):
        ir = _bridge_and_ir()
        first = project_fuzzed(ir, seed=42)
        second = project_fuzzed(ir, seed=42)
        self.assertEqual(first.view_id, second.view_id)
        self.assertNotEqual(project_fuzzed(ir, seed=7).view_id, first.view_id)

    def test_action_type_and_resource_class_subset_of_taxonomy(self):
        ir = _bridge_and_ir()
        for source in ("synthetic_compliant", "synthetic_violation", "fuzzed_envelope"):
            record = project_training_view(ir, source=source, seed=11)
            if record.action_type:
                self.assertIn(record.action_type, ACTION_TYPES)
            if record.resource_class:
                self.assertIn(record.resource_class, RESOURCE_CLASSES)

    def test_project_training_view_odl_trace_source(self):
        ir = _bridge_and_ir()
        record = project_training_view(
            ir,
            source="odl_trace",
            usage_mode="eval_harness",
            ledger_row={"action_type": "tool_call", "verb": "observe"},
        )
        self.assertEqual(record.source, "odl_trace")
        self.assertEqual(record.ir_fingerprint, ir["ir_fingerprint"])
        self.assertEqual(taxonomy_fingerprint(), taxonomy_fingerprint())


if __name__ == "__main__":
    unittest.main()
