"""Focused API tests for the reasoning exchange endpoint."""

from importlib.util import find_spec
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
import uuid

from pydantic import BaseModel


def _evolve_engine_schemas_available() -> bool:
    module = sys.modules.get("evolve_engine")
    if module is not None and not hasattr(module, "__path__"):
        sys.modules.pop("evolve_engine", None)
        sys.modules.pop("evolve_engine.schemas", None)
    try:
        return find_spec("evolve_engine.schemas") is not None
    except (ModuleNotFoundError, ValueError):
        return False


if not _evolve_engine_schemas_available():
    _evolve_engine_module = types.ModuleType("evolve_engine")
    _evolve_engine_schemas = types.ModuleType("evolve_engine.schemas")

    class _EvolutionRequest(BaseModel):
        job_id: str
        task: str
        config: dict = {}
        evaluation: dict = {}
        constraints: dict = {}
        jarvis_run_id: str | None = None


    class _EvolutionSuccessResponse(BaseModel):
        ok: bool | None = None


    class _EvolutionErrorResponse(BaseModel):
        error: str | None = None


    _evolve_engine_schemas.EvolutionRequest = _EvolutionRequest
    _evolve_engine_schemas.EvolutionSuccessResponse = _EvolutionSuccessResponse
    _evolve_engine_schemas.EvolutionErrorResponse = _EvolutionErrorResponse
    _evolve_engine_module.schemas = _evolve_engine_schemas
    sys.modules.setdefault("evolve_engine", _evolve_engine_module)
    sys.modules.setdefault("evolve_engine.schemas", _evolve_engine_schemas)

import src.api as api
from src.phase_gate import reset_registry


def _packet(*, version: str = "1.0") -> dict:
    return {
        "version": version,
        "type": "reasoning_packet",
        "id": str(uuid.uuid4()),
        "timestamp": "2026-04-25T14:00:00Z",
        "payload": {
            "claim": "The external system detected an interrupt.",
            "reasoning": "The interrupt signal and the new input arrived in the same bounded packet.",
            "evidence": ["interrupt_signal", "new_input"],
            "confidence": 0.84,
        },
        "meta": {
            "source": "external_reasoner",
            "domain": "operator_runtime",
            "tags": ["interrupt", "handoff"],
        },
    }


class TestReasoningExchangeApi(unittest.TestCase):
    """Verify the narrow reasoning exchange ingress path."""

    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="reasoning-exchange-api-"))
        self.original_module_governance_runtime_dir = api.module_governance.runtime_dir
        self.original_immune_runtime_dir = api.immune_system.runtime_dir
        self.original_detachment_guard_runtime_dir = api.cognitive_bridge_service.detachment_guard.runtime_dir
        api.module_governance.configure_runtime_dir(self.temp_root)
        api.module_governance.reset()
        api.immune_system.configure_runtime_dir(self.temp_root)
        api.immune_system.reset()
        api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(self.temp_root)
        api.cognitive_bridge_service.detachment_guard.reset()
        reset_registry()

    def tearDown(self):
        api.module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        api.module_governance.reset()
        api.immune_system.configure_runtime_dir(self.original_immune_runtime_dir)
        api.immune_system.reset()
        api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(self.original_detachment_guard_runtime_dir)
        api.cognitive_bridge_service.detachment_guard.reset()
        reset_registry()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_reasoning_evaluate_route_admits_valid_packet(self):
        with api.app.test_client() as client:
            response = client.post("/api/reasoning/evaluate", json=_packet())

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ADMIT")
        self.assertEqual(payload["reason"], "packet_meets_ingress_threshold")
        self.assertEqual(payload["cognitive_bridge"]["decision"], "ALLOW")
        self.assertEqual(
            payload["cognitive_bridge"]["governance_packet"]["packet_type"],
            "reasoning_packet_ingress",
        )
        self.assertEqual(payload["verification_gate"]["decision"], "ELIGIBLE")
        self.assertEqual(payload["module_governance"]["decision"], "ALLOW")
        self.assertIsNone(payload["immune_update"])

    def test_reasoning_evaluate_route_rejects_unsupported_version_before_governance(self):
        with api.app.test_client() as client:
            response = client.post("/api/reasoning/evaluate", json=_packet(version="2.0"))

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "REJECT")
        self.assertEqual(payload["reason"], "unsupported_version")
        self.assertEqual(payload["immune_update"]["event"]["action"], "observe_protocol_signal")
        self.assertEqual(payload["immune_update"]["event"]["details"]["signal_type"], "unsupported_version")
        self.assertIsNone(api.module_governance.get_module("aais.reasoning_exchange_protocol"))

    def test_reasoning_evaluate_route_fails_fast_on_malformed_packet(self):
        packet = _packet()
        del packet["payload"]["reasoning"]

        with api.app.test_client() as client:
            response = client.post("/api/reasoning/evaluate", json=packet)

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["status"], "INVALID")
        self.assertIn("payload is missing required fields", payload["reason"])
        self.assertEqual(payload["cognitive_bridge"]["decision"], "ALLOW")
        self.assertEqual(payload["immune_update"]["event"]["action"], "observe_protocol_signal")
        self.assertEqual(payload["immune_update"]["event"]["details"]["signal_type"], "invalid_packet_structure")
        self.assertIsNone(api.module_governance.get_module("aais.reasoning_exchange_protocol"))

    def test_reasoning_evaluate_route_returns_governed_block_when_quarantined(self):
        with api.app.test_client() as client:
            first_response = client.post("/api/reasoning/evaluate", json=_packet())

        self.assertEqual(first_response.status_code, 200)
        api.module_governance.report_runtime_signal(
            "aais.reasoning_exchange_protocol",
            signal_type="scope_expansion",
            reason="Test quarantine for reasoning ingress.",
        )

        with api.app.test_client() as client:
            blocked_response = client.post("/api/reasoning/evaluate", json=_packet())

        self.assertEqual(blocked_response.status_code, 403)
        blocked_payload = blocked_response.get_json()
        self.assertEqual(blocked_payload["status"], "REJECT")
        self.assertEqual(blocked_payload["reason"], "module_governance_blocked")
        self.assertEqual(blocked_payload["module_governance"]["decision"], "BLOCK")
