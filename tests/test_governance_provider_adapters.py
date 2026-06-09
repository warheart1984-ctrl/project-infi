"""Tests for governance provider adapters."""

import unittest

from src.authority_mask_lowering import lower_authority_mask
from src.invariant_compiler import compile_from_ir
from tests.test_bridge_fixtures import build_test_ir
from src.providers.governance_adapters import (
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_RETRY,
    MASK_SURFACE_LOGIT,
    MASK_SURFACE_STRUCTURED,
    ProviderContext,
    ReferenceMockAdapter,
    StubGovernanceAdapter,
    apply_authority_mask,
    get_governance_adapter,
    merge_mask_into_messages,
    merge_mask_into_provider_request,
    run_decode_governance,
    validate_decoded_output,
)


def _ir_and_bundle():
    ir = build_test_ir(trace_id="trace-adapter-test")
    bundle = compile_from_ir(ir)
    return ir, bundle


class TestGovernanceProviderAdapters(unittest.TestCase):
    def test_reference_mock_masks_forbidden_verbs(self):
        ir, bundle = _ir_and_bundle()
        mask_spec = bundle["authority_mask_spec"]
        adapter = ReferenceMockAdapter()
        ctx = ProviderContext(provider_id="reference_mock", site_id="tool_call_schema")
        mask = adapter.apply_authority_mask(ctx, mask_spec)
        self.assertEqual(mask.mask_surface, MASK_SURFACE_LOGIT)
        self.assertTrue(mask.denied_token_ids)
        self.assertIn("forbidden_verbs", mask.schema_constraints)

    def test_reference_mock_rollback_after_checkpoint_failure(self):
        _, bundle = _ir_and_bundle()
        adapter = ReferenceMockAdapter()
        ctx = ProviderContext(
            provider_id="reference_mock",
            checkpoint_failures=({"name": "proposal_only", "status": "hard_fail"},),
            attempt=1,
        )
        decision = adapter.run_decode_governance(ctx, bundle)
        self.assertEqual(decision.decision, DECISION_RETRY)
        self.assertTrue(decision.sampling_tighten or decision.generation_overrides)

    def test_stub_returns_passthrough_allow(self):
        ir, bundle = _ir_and_bundle()
        mask_spec = lower_authority_mask(ir, {"site_id": "tool_call_schema"})
        adapter = StubGovernanceAdapter("openai_compatible")
        ctx = ProviderContext(provider_id="openai_compatible")
        mask = adapter.apply_authority_mask(ctx, mask_spec)
        self.assertEqual(mask.metadata.get("implementation"), "stub")
        decision = adapter.run_decode_governance(ctx, bundle)
        self.assertEqual(decision.decision, DECISION_ALLOW)

    def test_local_structured_output_surface(self):
        _, bundle = _ir_and_bundle()
        adapter = get_governance_adapter("local")
        ctx = ProviderContext(provider_id="local")
        mask = adapter.apply_authority_mask(ctx, bundle["authority_mask_spec"])
        self.assertEqual(mask.mask_surface, MASK_SURFACE_STRUCTURED)
        self.assertTrue(mask.instruction_fragments)
        merged = merge_mask_into_provider_request({"provider": "local"}, mask)
        self.assertIn("governance_schema_constraints", merged)
        messages = merge_mask_into_messages([{"role": "user", "content": "hi"}], mask)
        self.assertTrue(any("Governed decode" in str(m.get("content")) for m in messages))

    def test_validate_decoded_output_forbidden_verb(self):
        ir, bundle = _ir_and_bundle()
        violation = validate_decoded_output(
            ProviderContext(
                provider_id="local",
                decoded_output={"verb": "execute"},
            ),
            bundle["authority_mask_spec"],
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation.get("status"), "hard_fail")

    def test_registry_helpers_none_without_spec(self):
        ctx = ProviderContext(provider_id="local")
        self.assertIsNone(apply_authority_mask(ctx, None))
        self.assertIsNone(run_decode_governance(ctx, None))

    def test_block_when_rollback_budget_exhausted(self):
        _, bundle = _ir_and_bundle()
        bundle["rollback_policy"]["max_rollbacks"] = 0
        adapter = ReferenceMockAdapter()
        ctx = ProviderContext(
            provider_id="reference_mock",
            checkpoint_failures=({"name": "x", "status": "hard_fail"},),
            attempt=2,
        )
        decision = adapter.run_decode_governance(ctx, bundle)
        self.assertEqual(decision.decision, DECISION_BLOCK)


if __name__ == "__main__":
    unittest.main()
