"""Tests for decode governance executor rollback loop."""

import unittest
from unittest.mock import patch

from src.aais_governed_llm_module import propose_governed_llm_envelope
from src.decode_governance_executor import (
    DECODE_GOVERNANCE_EXECUTOR_VERSION,
    execute_with_decode_governance,
    run_checkpoint_validators,
)
from src.governance_ir import build_governance_ir
from src.invariant_compiler import compile_from_ir
from src.invariant_engine import InvariantEngine
from src.jarvis_detachment_guard import build_bridge_attestation
from pathlib import Path
import tempfile


def _fixtures():
    runtime_dir = Path(tempfile.mkdtemp(prefix="decode-gov-exec-"))
    payload = {
        "question": "What is the status?",
        "intent": "general_qa",
        "execution_intent": "observe",
        "trace_id": "trace-decode-1",
        "response_mode": "think",
        "provider_mode": "local_first",
        "bridge_attestation": build_bridge_attestation(
            ingress="unit_test",
            surface="decode_governance_test",
            source_id="trace-decode-1",
            route="tests.decode_governance",
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
        "packet_fingerprint": "fp-decode-001",
    }
    bridge = {
        "decision": "ALLOW",
        "runtime_context": "live_runtime",
        "execution_allowed": True,
        "normalized_input": normalized,
        "governance_packet": governance,
        "bridge_invariant": InvariantEngine.validate_bridge_packet(normalized, governance),
    }
    ir = build_governance_ir(bridge_result=bridge)
    bundle = compile_from_ir(ir)
    envelope = propose_governed_llm_envelope(bridge)
    return bridge, ir, bundle, envelope


class TestDecodeGovernanceExecutor(unittest.TestCase):
    def test_run_checkpoint_validators_passes_valid_envelope(self):
        bridge, _, bundle, envelope = _fixtures()
        results = run_checkpoint_validators(envelope, bridge_result=bridge, decode_bundle=bundle)
        self.assertTrue(all(item.get("status") != "hard_fail" for item in results))

    def test_execute_with_decode_governance_success_path(self):
        bridge, ir, bundle, envelope = _fixtures()

        def fake_generator(*_args, **_kwargs):
            return {
                "status": "EXECUTED",
                "content": "ok",
                "module_id": "test",
                "provider": "test",
            }

        with patch(
            "src.decode_governance_executor.llm_execution_enabled",
            return_value=True,
        ):
            result = execute_with_decode_governance(
                envelope,
                bridge_result=bridge,
                question="status?",
                governance_ir=ir,
                decode_bundle=bundle,
                generate_candidate=fake_generator,
            )
        self.assertEqual(result["status"], "EXECUTED")
        self.assertEqual(result["executor_version"], DECODE_GOVERNANCE_EXECUTOR_VERSION)
        self.assertIn("decode_governance", result)

    def test_execute_with_decode_governance_rollback_then_block(self):
        bridge, ir, bundle, envelope = _fixtures()
        bundle["rollback_policy"]["max_rollbacks"] = 1
        checkpoint_calls = {"n": 0}

        def checkpoint_side_effect(*_args, **_kwargs):
            checkpoint_calls["n"] += 1
            if checkpoint_calls["n"] <= 1:
                return [
                    {"name": "bridge_invariant", "status": "pass"},
                    {"name": "governed_llm_envelope", "status": "pass"},
                    {"name": "proposal_only", "status": "pass"},
                    {"name": "temperature_zero", "status": "pass"},
                ]
            return [{"name": "proposal_only", "status": "hard_fail", "details": "forced"}]

        def fake_generator(*_args, **_kwargs):
            return {
                "status": "EXECUTED",
                "content": "bad",
                "module_id": "test",
                "provider": "test",
            }

        with patch(
            "src.decode_governance_executor.llm_execution_enabled",
            return_value=True,
        ), patch(
            "src.decode_governance_executor.run_checkpoint_validators",
            side_effect=checkpoint_side_effect,
        ):
            result = execute_with_decode_governance(
                envelope,
                bridge_result=bridge,
                question="status?",
                governance_ir=ir,
                decode_bundle=bundle,
                generate_candidate=fake_generator,
            )
        self.assertIn(result["status"], {"BLOCKED", "ESCALATED"})
        self.assertIn("decode_governance", result)
        self.assertGreaterEqual(len(result["decode_governance"].get("rollbacks_applied") or []), 1)

    def test_adapter_driven_retry_records_adapter_decision(self):
        bridge, ir, bundle, envelope = _fixtures()
        bundle["rollback_policy"]["max_rollbacks"] = 2
        checkpoint_calls = {"n": 0}

        def checkpoint_side_effect(*_args, **_kwargs):
            checkpoint_calls["n"] += 1
            if checkpoint_calls["n"] == 1:
                return [
                    {"name": "bridge_invariant", "status": "pass"},
                    {"name": "governed_llm_envelope", "status": "pass"},
                    {"name": "proposal_only", "status": "pass"},
                    {"name": "temperature_zero", "status": "pass"},
                ]
            return [{"name": "proposal_only", "status": "hard_fail", "details": "forced"}]

        def fake_generator(*_args, **_kwargs):
            return {
                "status": "EXECUTED",
                "content": "retry-me",
                "module_id": "test",
                "provider": "reference_mock",
            }

        with patch(
            "src.decode_governance_executor.llm_execution_enabled",
            return_value=True,
        ), patch(
            "src.decode_governance_executor.run_checkpoint_validators",
            side_effect=checkpoint_side_effect,
        ):
            result = execute_with_decode_governance(
                envelope,
                bridge_result=bridge,
                question="status?",
                governance_ir=ir,
                decode_bundle=bundle,
                generate_candidate=fake_generator,
            )
        rollbacks = result["decode_governance"].get("rollbacks_applied") or []
        flat_rollbacks = [
            str(entry)
            for group in rollbacks
            for entry in (group if isinstance(group, list) else [group])
        ]
        self.assertTrue(any(entry.startswith("adapter:") for entry in flat_rollbacks))

    def test_backward_compatible_without_authority_mask_spec(self):
        bridge, ir, bundle, envelope = _fixtures()
        bundle.pop("authority_mask_spec", None)
        checkpoint_calls = {"n": 0}

        def checkpoint_side_effect(*_args, **_kwargs):
            checkpoint_calls["n"] += 1
            if checkpoint_calls["n"] == 1:
                return [
                    {"name": "bridge_invariant", "status": "pass"},
                    {"name": "governed_llm_envelope", "status": "pass"},
                    {"name": "proposal_only", "status": "pass"},
                    {"name": "temperature_zero", "status": "pass"},
                ]
            return [{"name": "proposal_only", "status": "hard_fail", "details": "forced"}]

        def fake_generator(*_args, **_kwargs):
            return {
                "status": "EXECUTED",
                "content": "bad",
                "module_id": "test",
                "provider": "test",
            }

        with patch(
            "src.decode_governance_executor.llm_execution_enabled",
            return_value=True,
        ), patch(
            "src.decode_governance_executor.run_checkpoint_validators",
            side_effect=checkpoint_side_effect,
        ):
            result = execute_with_decode_governance(
                envelope,
                bridge_result=bridge,
                question="status?",
                governance_ir=ir,
                decode_bundle=bundle,
                generate_candidate=fake_generator,
            )
        rollbacks = result["decode_governance"].get("rollbacks_applied") or []
        self.assertFalse(any(str(item).startswith("adapter:") for item in rollbacks))


if __name__ == "__main__":
    unittest.main()
