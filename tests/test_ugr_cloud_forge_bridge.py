"""Tests for UGR Cloud Forge bridge integration."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.cloud_forge.failsafe import FORCE_SAFE_ENV
from src.cognitive_bridge import CognitiveBridgeService
from src.immune_system import ImmuneSystemController
from src.jarvis_detachment_guard import JarvisDetachmentGuard
from src.module_governance import module_governance
from src.phase_gate import reset_registry
from src.ugr.cloud_forge_bridge import (
    build_ugr_law_envelope,
    build_ugr_task_signature,
    cloud_forge_enabled,
    rail_trace_summary,
    schedule_rail_for_ugr,
)
from src.ugr.unified_runtime import UnifiedGovernedRuntime


class TestUGRCloudForgeBridge(unittest.TestCase):
    def test_build_task_signature_for_deliberation(self):
        task = build_ugr_task_signature(
            {
                "question": "What caused the latency spike?",
                "intent": "diagnose_runtime",
                "context": {"component": "orchestrator"},
            },
            trace_id="ugr-test-1",
        )
        self.assertEqual(task["task_id"], "ugr-test-1")
        self.assertEqual(task["pattern_class"], "diagnose_runtime")
        self.assertEqual(task["mutation_scope"], "read")
        self.assertTrue(task["normalized_prompt_hash"])

    def test_required_proof_law_envelope_forces_high_risk_path(self):
        law = build_ugr_law_envelope({"intent": "general_qa", "context": {"required_proof": True}})
        bundle = schedule_rail_for_ugr(
            {"question": "Explain runtime law", "intent": "general_qa", "context": {"required_proof": True}},
            trace_id="ugr-proof-1",
        )
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle["rail_decision"]["rail"], "SAFE")
        self.assertTrue(law["required_proof"])

    def test_immune_elevated_forces_safe(self):
        bundle = schedule_rail_for_ugr(
            {"question": "Explain runtime law", "intent": "general_qa", "immune_elevated": True},
            trace_id="ugr-immune-1",
        )
        self.assertEqual(bundle["rail_decision"]["rail"], "SAFE")
        self.assertIn("immune.elevated", bundle["rail_decision"]["rationale_codes"])

    @mock.patch.dict(os.environ, {FORCE_SAFE_ENV: "1"}, clear=False)
    def test_force_safe_env_forces_safe(self):
        bundle = schedule_rail_for_ugr(
            {"question": "Explain runtime law", "intent": "general_qa"},
            trace_id="ugr-failsafe-1",
        )
        self.assertEqual(bundle["rail_decision"]["rail"], "SAFE")
        self.assertIn("failsafe.force_safe", bundle["rail_decision"]["rationale_codes"])

    def test_rail_trace_summary_is_compact(self):
        bundle = schedule_rail_for_ugr(
            {"question": "Explain runtime law", "intent": "general_qa"},
            trace_id="ugr-summary-1",
        )
        summary = rail_trace_summary(bundle)
        self.assertIn("rail", summary)
        self.assertIn("risk", summary)
        self.assertIn("rationale_codes", summary)
        self.assertNotIn("cognition_plan", summary)


class TestUGRRuntimeCloudForgeIntegration(unittest.TestCase):
    def setUp(self):
        self._temp_roots: list[Path] = []
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        os.environ.pop("UGR_CLOUD_FORGE_ENABLED", None)

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        module_governance.reset()
        reset_registry()
        os.environ.pop("UGR_CLOUD_FORGE_ENABLED", None)
        os.environ.pop(FORCE_SAFE_ENV, None)
        for temp_root in self._temp_roots:
            shutil.rmtree(temp_root, ignore_errors=True)

    def _make_runtime(self) -> UnifiedGovernedRuntime:
        temp_root = Path(tempfile.mkdtemp(prefix="ugr-cf-runtime-"))
        self._temp_roots.append(temp_root)
        module_governance.configure_runtime_dir(temp_root)
        module_governance.reset()
        reset_registry()
        bridge = CognitiveBridgeService(
            immune_controller=ImmuneSystemController(runtime_dir=temp_root),
            detachment_guard=JarvisDetachmentGuard(runtime_dir=temp_root),
        )
        return UnifiedGovernedRuntime(bridge=bridge, runtime_dir=temp_root)

    def test_handle_request_includes_rail_decision(self):
        runtime = self._make_runtime()
        result = runtime.handle_request(
            {
                "question": "What likely caused the runtime latency spike?",
                "intent": "diagnose_runtime",
                "tenant_id": "default",
                "context": {"component": "orchestrator"},
                "lane_types": ["symbolic", "graph"],
            }
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("rail_decision", result)
        self.assertIn("cloud_forge", result)
        self.assertEqual(result["rail_decision"]["task_id"], result["trace_id"])
        self.assertIn(result["rail_decision"]["rail"], {"SAFE", "NORMAL", "EXPRESS"})

    def test_rail_decision_is_deterministic_for_same_request(self):
        request = {
            "question": "What likely caused the runtime latency spike?",
            "intent": "diagnose_runtime",
            "tenant_id": "default",
            "context": {"component": "orchestrator"},
            "lane_types": ["symbolic"],
        }
        first = self._make_runtime().handle_request(request)
        second = self._make_runtime().handle_request(request)
        self.assertEqual(first["rail_decision"]["rail"], second["rail_decision"]["rail"])
        self.assertEqual(
            first["rail_decision"]["rationale_codes"],
            second["rail_decision"]["rationale_codes"],
        )

    def test_trace_jsonl_contains_rail_decision_summary(self):
        runtime = self._make_runtime()
        result = runtime.handle_request(
            {
                "question": "Explain governed runtime convergence",
                "intent": "general_qa",
            }
        )
        trace_lines = runtime.traces_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertTrue(trace_lines)
        trace = json.loads(trace_lines[-1])
        self.assertEqual(trace["trace_id"], result["trace_id"])
        self.assertIn("rail_decision", trace)
        self.assertEqual(trace["rail_decision"]["rail"], result["rail_decision"]["rail"])

    @mock.patch.dict(os.environ, {"UGR_CLOUD_FORGE_ENABLED": "0"}, clear=False)
    def test_cloud_forge_can_be_disabled(self):
        self.assertFalse(cloud_forge_enabled())
        runtime = self._make_runtime()
        result = runtime.handle_request({"question": "Explain runtime law", "intent": "general_qa"})
        self.assertNotIn("rail_decision", result)
        self.assertNotIn("cloud_forge", result)


if __name__ == "__main__":
    unittest.main()
