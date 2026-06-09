"""Tests for invariant compiler and ingress/admission helpers."""

import unittest

from src.governance_ir import build_governance_ir
from src.governance_taxonomy import TAXONOMY_SCHEMA_ID, taxonomy_fingerprint
from src.invariant_compiler import (
    INVARIANT_COMPILER_VERSION,
    InvariantCompilerError,
    apply_ingress_plan,
    compile_from_ir,
    run_admission_checks,
)
from src.jarvis_detachment_guard import build_bridge_attestation
from pathlib import Path
import tempfile


def _bridge_and_ir():
    runtime_dir = Path(tempfile.mkdtemp(prefix="inv-compiler-test-"))
    payload = {
        "question": "Summarize runtime health.",
        "intent": "general_qa",
        "execution_intent": "observe",
        "trace_id": "trace-compiler-1",
        "bridge_attestation": build_bridge_attestation(
            ingress="unit_test",
            surface="invariant_compiler_test",
            source_id="trace-compiler-1",
            route="tests.invariant_compiler",
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
        "packet_fingerprint": "fp-compiler-001",
    }
    bridge = {
        "normalized_input": normalized,
        "governance_packet": governance,
    }
    ir = build_governance_ir(bridge_result=bridge)
    return normalized, governance, ir


class TestInvariantCompiler(unittest.TestCase):
    def test_compile_from_ir_emits_decode_bundle(self):
        _, _, ir = _bridge_and_ir()
        bundle = compile_from_ir(ir)
        self.assertEqual(bundle["compiler_version"], INVARIANT_COMPILER_VERSION)
        self.assertEqual(bundle["ir_fingerprint"], ir["ir_fingerprint"])
        self.assertIn("check_graph", bundle)
        self.assertIn("rollback_policy", bundle)
        self.assertIn("escalation_hooks", bundle)
        self.assertIn("ingress_plan", bundle)
        self.assertEqual(bundle["taxonomy_ref"], TAXONOMY_SCHEMA_ID)
        self.assertEqual(bundle["authority_mask_spec"]["status"], "compilable_target")
        self.assertEqual(bundle["training_view_spec"]["status"], "compilable_target")
        self.assertEqual(bundle["authority_mask_spec"]["ir_fingerprint"], ir["ir_fingerprint"])
        self.assertEqual(bundle["training_view_spec"]["ir_fingerprint"], ir["ir_fingerprint"])
        self.assertEqual(
            bundle["authority_mask_spec"]["taxonomy_fingerprint"],
            taxonomy_fingerprint(),
        )
        self.assertEqual(
            bundle["training_view_spec"]["taxonomy_fingerprint"],
            taxonomy_fingerprint(),
        )
        self.assertEqual(
            bundle["authority_mask_spec"]["taxonomy_fingerprint"],
            bundle["training_view_spec"]["taxonomy_fingerprint"],
        )
        self.assertIn("maskable_sites", bundle["authority_mask_spec"])
        self.assertIn("example_record", bundle["training_view_spec"])

    def test_compile_from_ir_rejects_bad_version(self):
        with self.assertRaises(InvariantCompilerError):
            compile_from_ir({"ir_version": "legacy", "ir_fingerprint": "abc"})

    def test_apply_ingress_plan_matches_bridge_invariant(self):
        normalized, governance, ir = _bridge_and_ir()
        bundle = compile_from_ir(ir)
        ingress = apply_ingress_plan(normalized, governance, decode_bundle=bundle)
        self.assertTrue(ingress["allows"])
        bridge_result = next(
            item for item in ingress["results"] if item.get("validator") == "bridge_invariant"
        )
        self.assertTrue(bridge_result.get("allows"))

    def test_run_admission_checks_passes_for_valid_packet(self):
        normalized, governance, ir = _bridge_and_ir()
        bundle = compile_from_ir(ir)
        admission = run_admission_checks(normalized, governance, decode_bundle=bundle)
        self.assertTrue(admission["allows"])


if __name__ == "__main__":
    unittest.main()
