"""Tests for authority mask lowering and get_authority_mask hook."""

import copy
import unittest
from pathlib import Path
import tempfile

from src.authority_mask_lowering import get_authority_mask, lower_authority_mask
from src.governance_ir import build_governance_ir
from src.governance_taxonomy import taxonomy_fingerprint
from src.jarvis_detachment_guard import build_bridge_attestation


def _bridge_and_ir(*, execution_intent: str = "observe", effectful: bool = False):
    runtime_dir = Path(tempfile.mkdtemp(prefix="mask-lowering-test-"))
    payload = {
        "question": "Summarize runtime health.",
        "intent": "general_qa",
        "execution_intent": execution_intent,
        "trace_id": "trace-mask-1",
        "bridge_attestation": build_bridge_attestation(
            ingress="unit_test",
            surface="authority_mask_test",
            source_id="trace-mask-1",
            route="tests.test_authority_mask_lowering",
            intent=execution_intent,
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
        "execution_intent": execution_intent,
        "runtime_context": "live_runtime",
        "effectful": effectful,
        "requires_approval": effectful,
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
        "packet_fingerprint": "fp-mask-001",
    }
    bridge = {
        "normalized_input": normalized,
        "governance_packet": governance,
    }
    return build_governance_ir(bridge_result=bridge)


class TestAuthorityMaskLowering(unittest.TestCase):
    def test_lower_authority_mask_is_deterministic(self):
        ir = _bridge_and_ir()
        first = lower_authority_mask(ir, {})
        second = lower_authority_mask(ir, {})
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "compilable_target")
        self.assertEqual(first["taxonomy_fingerprint"], taxonomy_fingerprint())

    def test_get_authority_mask_matches_lowered_dict(self):
        ir = _bridge_and_ir()
        lowered = lower_authority_mask(ir, {"site_id": "tool_call_schema"})
        spec = get_authority_mask(ir, {"site_id": "tool_call_schema"})
        self.assertEqual(spec.mask_id, lowered["mask_id"])
        self.assertEqual(spec.ir_fingerprint, lowered["ir_fingerprint"])
        self.assertEqual(spec.status, "compilable_target")

    def test_execute_intent_allows_external_mutation_site(self):
        ir = _bridge_and_ir(execution_intent="execute", effectful=True)
        mask = lower_authority_mask(ir, {})
        external = mask["sites"]["external_mutation_command"]
        self.assertFalse(external.get("denied"))
        self.assertIn("execute", external.get("allowed_verbs", ()))

    def test_observe_only_denies_execute_on_external_mutation(self):
        ir = _bridge_and_ir(execution_intent="observe")
        ir = copy.deepcopy(ir)
        ir["execution_context"]["otem_level"] = "blocked"
        mask = lower_authority_mask(ir, {})
        external = mask["sites"]["external_mutation_command"]
        self.assertFalse(external.get("allowed_verbs"))

    def test_subagent_depth_zero_denies_spawn_descriptor(self):
        ir = _bridge_and_ir()
        ir = copy.deepcopy(ir)
        ir["authority_envelope"]["max_subagent_depth"] = 0
        mask = lower_authority_mask(ir, {})
        spawn = mask["sites"]["subagent_spawn_descriptor"]
        self.assertTrue(spawn.get("denied"))
        self.assertEqual(spawn.get("max_child_scope"), 0)

    def test_cisiv_concept_restricts_action_classes_vs_implementation(self):
        ir_concept = _bridge_and_ir(execution_intent="execute", effectful=True)
        ir_concept = copy.deepcopy(ir_concept)
        ir_concept["execution_context"]["cisiv_stage"] = "concept"

        ir_impl = _bridge_and_ir(execution_intent="execute", effectful=True)

        concept_site = lower_authority_mask(ir_concept, {})["sites"]["cisiv_stage_transition"]
        impl_site = lower_authority_mask(ir_impl, {})["sites"]["cisiv_stage_transition"]

        self.assertEqual(set(concept_site.get("allowed_action_classes")), {"observe"})
        self.assertIn("execute", impl_site.get("allowed_action_classes"))


if __name__ == "__main__":
    unittest.main()
