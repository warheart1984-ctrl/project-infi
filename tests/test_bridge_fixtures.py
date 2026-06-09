"""Shared bridge/IR fixtures for governance unit tests."""

from __future__ import annotations

from pathlib import Path
import tempfile

from src.governance_ir import build_governance_ir
from src.invariant_engine import InvariantEngine
from src.jarvis_detachment_guard import build_bridge_attestation


def build_test_bridge(
    *,
    trace_id: str = "trace-governance-test",
    route: str = "tests.test_bridge_fixtures",
    surface: str = "governance_test",
) -> dict:
    runtime_dir = Path(tempfile.mkdtemp(prefix="gov-test-bridge-"))
    payload = {
        "question": "What is the status?",
        "intent": "general_qa",
        "execution_intent": "observe",
        "trace_id": trace_id,
        "response_mode": "think",
        "provider_mode": "local_first",
        "bridge_attestation": build_bridge_attestation(
            ingress="unit_test",
            surface=surface,
            source_id=trace_id,
            route=route,
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
        "packet_fingerprint": f"fp-{trace_id}",
    }
    bridge = {
        "decision": "ALLOW",
        "runtime_context": "live_runtime",
        "execution_allowed": True,
        "normalized_input": normalized,
        "governance_packet": governance,
        "bridge_invariant": InvariantEngine.validate_bridge_packet(normalized, governance),
    }
    return bridge


def build_test_ir(*, trace_id: str = "trace-governance-test") -> dict:
    return build_governance_ir(bridge_result=build_test_bridge(trace_id=trace_id))
