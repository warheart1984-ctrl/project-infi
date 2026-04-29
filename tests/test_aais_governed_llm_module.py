"""Tests for the proposal-only governed LLM seam."""

from pathlib import Path
import shutil
import tempfile
import unittest

from src.aais_governed_llm_module import (
    GOVERNED_LLM_MODULE_ID,
    propose_governed_llm_envelope,
    validate_governed_llm_envelope,
)
from src.governance_layer import GovernanceLayer
from src.immune_system import ImmuneSystemController
from src.module_governance import ModuleGovernanceController
from src.phase_gate import Phase, demote_component, reset_registry


def _bridge_result(
    *,
    packet_type: str = "generation_request",
    response_mode: str | None = "think",
    provider_mode: str | None = "local_first",
    runtime_context: str = "live_runtime",
    decision: str = "ALLOW",
) -> dict:
    payload = {
        "execution_intent": "respond",
    }
    if response_mode is not None:
        payload["response_mode"] = response_mode
    if provider_mode is not None:
        payload["provider_mode"] = provider_mode
    return {
        "decision": decision,
        "runtime_context": runtime_context,
        "execution_allowed": decision != "BLOCK",
        "normalized_input": {
            "source": "llm",
            "type": packet_type,
            "payload": payload,
        },
        "governance_packet": {
            "source": "llm",
            "packet_type": packet_type,
            "execution_intent": "respond",
            "runtime_context": runtime_context,
            "effectful": False,
        },
    }


class TestAAISGovernedLLMModule(unittest.TestCase):
    """Keep provider routing behind the bridge and inside a bounded envelope."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="governed-llm-"))
        self.immune = ImmuneSystemController(runtime_dir=self.temp_root)
        self.governance = GovernanceLayer(runtime_dir=self.temp_root)
        self.module_governance = ModuleGovernanceController(
            runtime_dir=self.temp_root,
            immune_controller=self.immune,
            governance_controller=self.governance,
        )
        self.immune.reset()
        self.governance.reset()
        self.module_governance.reset()
        reset_registry()

    def tearDown(self):
        reset_registry()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_generation_request_produces_bounded_local_proposal(self):
        payload = propose_governed_llm_envelope(
            _bridge_result(),
            module_governance_controller=self.module_governance,
        )

        self.assertEqual(payload["status"], "PROPOSED")
        self.assertEqual(payload["reason"], "bounded_provider_proposal_ready")
        self.assertTrue(payload["proposal_only"])
        self.assertEqual(payload["provider_request"]["provider"], "local")
        self.assertEqual(payload["provider_request"]["response_mode"], "think")
        self.assertEqual(payload["module_governance"]["decision"], "ALLOW")
        self.assertEqual(payload["phase_gate"]["decision"], "ALLOW")
        self.assertTrue(validate_governed_llm_envelope(payload))

    def test_deliberation_request_defaults_to_think_mode(self):
        payload = propose_governed_llm_envelope(
            _bridge_result(packet_type="deliberation_request", response_mode=None),
            module_governance_controller=self.module_governance,
        )

        self.assertEqual(payload["status"], "PROPOSED")
        self.assertEqual(payload["provider_request"]["response_mode"], "think")

    def test_unsupported_packet_type_fails_closed(self):
        payload = propose_governed_llm_envelope(
            _bridge_result(packet_type="operator_turn"),
            module_governance_controller=self.module_governance,
        )

        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["reason"], "verification_gate_blocked")
        self.assertEqual(payload["verification_gate"]["decision"], "BLOCK")
        self.assertIsNone(payload["provider_request"])
        self.assertTrue(validate_governed_llm_envelope(payload))

    def test_phase_gate_rollback_blocks_live_proposal(self):
        propose_governed_llm_envelope(
            _bridge_result(),
            module_governance_controller=self.module_governance,
        )
        demote_component(
            GOVERNED_LLM_MODULE_ID,
            Phase.VALIDATED,
            reason="Rollback governed LLM seam to guarded operator-only evaluation.",
        )

        payload = propose_governed_llm_envelope(
            _bridge_result(),
            module_governance_controller=self.module_governance,
        )

        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["reason"], "phase_gate_blocked")
        self.assertEqual(payload["phase_gate"]["decision"], "BLOCK")

    def test_quarantined_module_blocks_proposal(self):
        propose_governed_llm_envelope(
            _bridge_result(),
            module_governance_controller=self.module_governance,
        )
        self.module_governance.report_runtime_signal(
            GOVERNED_LLM_MODULE_ID,
            signal_type="scope_expansion",
            reason="Test quarantine for governed LLM seam.",
        )

        payload = propose_governed_llm_envelope(
            _bridge_result(),
            module_governance_controller=self.module_governance,
        )

        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["reason"], "module_governance_blocked")
        self.assertEqual(payload["module_governance"]["decision"], "BLOCK")
