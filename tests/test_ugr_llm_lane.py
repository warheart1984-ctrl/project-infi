"""Tests for UGR governed LLM lane v1."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.aais_governed_llm_module import GOVERNED_LLM_MODULE_ID, validate_governed_llm_envelope
from src.immune_system import ImmuneSystemController
from src.module_governance import ModuleGovernanceController
from src.phase_gate import reset_registry
from src.ugr.convergence_engine import converge_lane_results
from src.ugr.lane_manager import LaneSpec, run_lanes, run_llm_lane
from src.ugr.llm_lane import (
    UGR_LLM_GENERATION_OVERRIDES,
    UGR_LLM_TEMPERATURE,
    apply_ugr_temperature_cap,
    build_bridge_result_for_llm_lane,
    run_governed_llm_lane,
)
from src.ugr.pattern_ledger import PatternLedgerStore


class TestUGRGovernedLLMLane(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-llm-lane-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        self.spec = LaneSpec(lane_id="lane-llm-0", lane_type="llm")
        self.shared_context = {
            "trace_id": "trace-llm-1",
            "question": "What likely caused the runtime latency spike?",
            "intent": "diagnose_runtime",
            "tenant_id": "default",
            "context": {"component": "orchestrator"},
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)
        reset_registry()

    def test_lane_produces_governed_proposal_envelope(self):
        result = run_governed_llm_lane(self.spec, self.shared_context)
        self.assertEqual(result.status, "success")
        envelope = result.payload.get("governed_llm") or {}
        self.assertEqual(envelope.get("status"), "PROPOSED")
        self.assertTrue(validate_governed_llm_envelope(envelope))
        self.assertTrue(envelope.get("proposal_only"))
        claims = result.payload.get("claims") or []
        self.assertGreaterEqual(len(claims), 2)
        self.assertTrue(any(item.get("predicate") == "suggested_next_step" for item in claims))

    def test_lane_output_is_deterministic(self):
        first = run_governed_llm_lane(self.spec, self.shared_context)
        second = run_governed_llm_lane(self.spec, self.shared_context)
        first_claims = first.payload.get("claims") or []
        second_claims = second.payload.get("claims") or []
        self.assertEqual(
            [(item.get("predicate"), item.get("object")) for item in first_claims],
            [(item.get("predicate"), item.get("object")) for item in second_claims],
        )

    def test_temperature_zero_is_enforced(self):
        result = run_governed_llm_lane(self.spec, self.shared_context)
        envelope = result.payload.get("governed_llm") or {}
        overrides = dict((envelope.get("provider_request") or {}).get("generation_overrides") or {})
        self.assertLessEqual(float(overrides.get("temperature", 1.0)), UGR_LLM_TEMPERATURE)
        self.assertLessEqual(float(overrides.get("temperature_max", 1.0)), UGR_LLM_TEMPERATURE)
        invariant_names = {item.get("name") for item in result.invariant_results}
        self.assertIn("temperature_zero", invariant_names)

    def test_apply_ugr_temperature_cap(self):
        capped = apply_ugr_temperature_cap({"generation_overrides": {"temperature_max": 0.32}})
        self.assertEqual(capped["generation_overrides"], UGR_LLM_GENERATION_OVERRIDES)

    def test_blocked_when_bridge_packet_is_unsupported(self):
        bridge_result = build_bridge_result_for_llm_lane(self.shared_context)
        bridge_result["governance_packet"]["packet_type"] = "operator_turn"
        context = dict(self.shared_context)
        context["bridge_result"] = bridge_result
        result = run_governed_llm_lane(self.spec, context)
        self.assertEqual(result.status, "blocked")
        self.assertEqual((result.payload.get("governed_llm") or {}).get("status"), "BLOCKED")
        self.assertEqual(result.payload.get("claims"), [])

    def test_immune_elevated_adds_flags(self):
        context = dict(self.shared_context)
        context["immune_elevated"] = True
        result = run_governed_llm_lane(self.spec, context)
        self.assertTrue(result.immune_flags)
        self.assertEqual(result.immune_flags[0].get("type"), "immune_elevated")

    def test_blocked_when_governed_llm_module_is_quarantined(self):
        immune = ImmuneSystemController(runtime_dir=self.temp_root)
        module_governance = ModuleGovernanceController(runtime_dir=self.temp_root, immune_controller=immune)
        module_governance.reset()
        reset_registry()
        run_governed_llm_lane(
            self.spec,
            self.shared_context,
            module_governance_controller=module_governance,
        )
        module_governance.report_runtime_signal(
            GOVERNED_LLM_MODULE_ID,
            signal_type="scope_expansion",
            reason="Test quarantine for UGR LLM lane.",
        )
        result = run_governed_llm_lane(
            self.spec,
            self.shared_context,
            module_governance_controller=module_governance,
        )
        self.assertEqual(result.status, "blocked")
        self.assertEqual((result.payload.get("governed_llm") or {}).get("status"), "BLOCKED")
        self.assertEqual(result.payload.get("claims"), [])


class TestUGRLLMLaneConvergence(unittest.TestCase):
    def test_symbolic_precedence_over_llm_on_conflict(self):
        lane_results = [
            {
                "lane_id": "lane-llm",
                "lane_type": "llm",
                "status": "success",
                "metrics": {},
                "invariant_results": [],
                "immune_flags": [],
                "payload": {
                    "claims": [
                        {
                            "id": "c-llm",
                            "subject": "root cause",
                            "predicate": "identified_as",
                            "object": "unknown hypothesis",
                            "confidence": 0.9,
                            "source_lane": "llm",
                            "evidence_refs": ["llm:1"],
                        }
                    ]
                },
            },
            {
                "lane_id": "lane-symbolic",
                "lane_type": "symbolic",
                "status": "success",
                "metrics": {},
                "invariant_results": [],
                "immune_flags": [],
                "payload": {
                    "claims": [
                        {
                            "id": "c-sym",
                            "subject": "root cause",
                            "predicate": "identified_as",
                            "object": "config regression",
                            "confidence": 0.85,
                            "source_lane": "symbolic",
                            "evidence_refs": ["sym:1"],
                        }
                    ]
                },
            },
        ]
        merged = converge_lane_results("trace-merge", lane_results)
        accepted = [item for item in merged["final_beliefs"] if item["status"] in {"accepted", "contested"}]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["object"], "config regression")
        self.assertIn("lane-symbolic", accepted[0]["supporting_lanes"])

    def test_run_lanes_includes_governed_llm_payload(self):
        temp_root = Path(tempfile.mkdtemp(prefix="ugr-llm-lanes-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(temp_root)
        try:
            ledger = PatternLedgerStore(runtime_dir=temp_root)
            specs = [LaneSpec(lane_id="lane-llm", lane_type="llm")]
            context = {
                "question": "Explain governed runtime convergence",
                "intent": "general_qa",
                "context": {},
            }
            results = run_lanes("trace-llm", specs, context, ledger=ledger)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, "success")
            self.assertIn("governed_llm", results[0].payload)
        finally:
            os.environ.pop("AAIS_RUNTIME_DIR", None)
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
