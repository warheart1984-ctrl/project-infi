"""Tests for governed LLM executor adapter mask merge."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aais_governed_llm_module import propose_governed_llm_envelope
from src.governance_ir import build_governance_ir
from src.invariant_compiler import compile_from_ir
from src.jarvis_detachment_guard import build_bridge_attestation
from src.ugr.governed_llm_executor import execute_governed_llm_proposal
from pathlib import Path
import tempfile


def _fixtures(provider_id: str = "local"):
    runtime_dir = Path(tempfile.mkdtemp(prefix="governed-llm-adapter-"))
    payload = {
        "question": "status?",
        "intent": "general_qa",
        "execution_intent": "observe",
        "trace_id": "trace-llm-adapter-1",
        "provider_mode": provider_id,
        "bridge_attestation": build_bridge_attestation(
            ingress="unit_test",
            surface="governed_llm_adapter_test",
            source_id="trace-llm-adapter-1",
            route="tests.test_governed_llm_executor_adapters",
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
        "packet_fingerprint": "fp-llm-adapter-001",
    }
    bridge = {
        "decision": "ALLOW",
        "runtime_context": "live_runtime",
        "execution_allowed": True,
        "normalized_input": normalized,
        "governance_packet": governance,
    }
    ir = build_governance_ir(bridge_result=bridge)
    bundle = compile_from_ir(ir)
    bridge["decode_governance_bundle"] = bundle
    envelope = propose_governed_llm_envelope(bridge)
    envelope["provider_request"] = {
        **dict(envelope.get("provider_request") or {}),
        "provider": provider_id,
    }
    return bridge, envelope


class TestGovernedLlmExecutorAdapters(unittest.TestCase):
    def test_executor_includes_provider_mask_when_bundle_present(self):
        bridge, envelope = _fixtures("local")
        mock_response = MagicMock()
        mock_response.content = "ok"
        mock_response.model = "test-model"
        mock_response.input_tokens = 1
        mock_response.output_tokens = 2

        mock_adapter = MagicMock()
        mock_adapter.invoke = AsyncMock(return_value=mock_response)
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_adapter
        mock_registry.can_invoke.return_value = True

        with patch("src.ugr.governed_llm_executor.llm_execution_enabled", return_value=True):
            result = execute_governed_llm_proposal(
                envelope,
                bridge_result=bridge,
                question="status?",
                provider_registry_instance=mock_registry,
                force_execute=True,
            )
        self.assertEqual(result["status"], "EXECUTED")
        self.assertIn("provider_mask", result)
        self.assertEqual(result["provider_mask"]["mask_surface"], "structured_output")
        request = result.get("provider_request") or {}
        self.assertIn("governance_schema_constraints", request)

    def test_executor_without_mask_spec_backward_compatible(self):
        bridge, envelope = _fixtures("local")
        bridge.pop("decode_governance_bundle", None)
        mock_response = MagicMock()
        mock_response.content = "ok"
        mock_response.model = "test-model"
        mock_response.input_tokens = 1
        mock_response.output_tokens = 2

        mock_adapter = MagicMock()
        mock_adapter.invoke = AsyncMock(return_value=mock_response)
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_adapter
        mock_registry.can_invoke.return_value = True

        with patch("src.ugr.governed_llm_executor.llm_execution_enabled", return_value=True):
            result = execute_governed_llm_proposal(
                envelope,
                bridge_result=bridge,
                question="status?",
                provider_registry_instance=mock_registry,
                force_execute=True,
            )
        self.assertEqual(result["status"], "EXECUTED")
        self.assertNotIn("provider_mask", result)


if __name__ == "__main__":
    unittest.main()
