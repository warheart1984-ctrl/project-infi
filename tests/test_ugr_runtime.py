"""Tests for Unified Governed Runtime walking skeleton."""

import shutil
import tempfile
import unittest
from pathlib import Path

from src.cognitive_bridge import DECISION_BLOCK
from src.cognitive_bridge import CognitiveBridgeService
from src.immune_system import ImmuneSystemController
from src.jarvis_detachment_guard import JarvisDetachmentGuard, build_bridge_attestation
from src.module_governance import module_governance
from src.phase_gate import reset_registry
from src.ugr.convergence_engine import converge_lane_results
from src.ugr.lane_manager import LaneSpec, run_lanes, run_symbolic_lane
from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.unified_runtime import UnifiedGovernedRuntime


class TestUGRPatternLedger(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-ledger-"))

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_append_and_query_claims(self):
        ledger = PatternLedgerStore(runtime_dir=self.temp_root)
        ledger.append_claim(
            {
                "claim_id": "claim-test-1",
                "subject": "runtime orchestrator",
                "predicate": "latency_spike",
                "object": "observed after deploy",
                "confidence": 0.8,
                "source_lane": "graph",
                "evidence_refs": ["evidence:1"],
                "tenant_scope": "global",
                "status": "accepted",
            }
        )
        matches = ledger.query_by_subject("runtime orchestrator")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["predicate"], "latency_spike")


class TestUGRLanes(unittest.TestCase):
    def test_symbolic_lane_flags_policy_violation(self):
        spec = LaneSpec(lane_id="sym-1", lane_type="symbolic")
        result = run_symbolic_lane(
            spec,
            {
                "question": "Why is the node unhealthy?",
                "tenant_id": "default",
                "context": {"violates_policy": True},
            },
        )
        constraints = result.payload.get("constraints") or []
        self.assertTrue(any(item.get("violated") for item in constraints))

    def test_parallel_lanes_are_deterministically_ordered(self):
        ledger = PatternLedgerStore(runtime_dir=Path(tempfile.mkdtemp(prefix="ugr-lanes-")))
        specs = [
            LaneSpec(lane_id="lane-a", lane_type="llm"),
            LaneSpec(lane_id="lane-b", lane_type="symbolic"),
            LaneSpec(lane_id="lane-c", lane_type="graph"),
        ]
        context = {"question": "diagnose runtime drift", "intent": "diagnose_runtime", "context": {}}
        first = run_lanes("trace-1", specs, context, ledger=ledger)
        second = run_lanes("trace-1", specs, context, ledger=ledger)
        self.assertEqual([lane.lane_id for lane in first], [lane.lane_id for lane in second])


class TestUGRConvergence(unittest.TestCase):
    def test_symbolic_precedence_on_conflict(self):
        lane_results = [
            {
                "lane_id": "lane-llm",
                "lane_type": "llm",
                "status": "success",
                "payload": {
                    "claims": [
                        {
                            "id": "c-llm",
                            "subject": "root cause",
                            "predicate": "identified_as",
                            "object": "memory leak",
                            "confidence": 0.9,
                            "evidence_refs": ["llm:1"],
                        }
                    ]
                },
                "invariant_results": [],
                "immune_flags": [],
            },
            {
                "lane_id": "lane-symbolic",
                "lane_type": "symbolic",
                "status": "success",
                "payload": {
                    "claims": [
                        {
                            "id": "c-sym",
                            "subject": "root cause",
                            "predicate": "identified_as",
                            "object": "config regression",
                            "confidence": 0.85,
                            "evidence_refs": ["sym:1"],
                        }
                    ]
                },
                "invariant_results": [],
                "immune_flags": [],
            },
        ]
        merged = converge_lane_results("trace-merge", lane_results)
        accepted = [item for item in merged["final_beliefs"] if item["status"] in {"accepted", "contested"}]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["object"], "config regression")
        self.assertIn("lane-symbolic", accepted[0]["supporting_lanes"])


class TestUGRUnifiedRuntime(unittest.TestCase):
    def _make_runtime(self) -> UnifiedGovernedRuntime:
        temp_root = Path(tempfile.mkdtemp(prefix="ugr-runtime-"))
        self._temp_roots.append(temp_root)
        module_governance.configure_runtime_dir(temp_root)
        module_governance.reset()
        reset_registry()
        bridge = CognitiveBridgeService(
            immune_controller=ImmuneSystemController(runtime_dir=temp_root),
            detachment_guard=JarvisDetachmentGuard(runtime_dir=temp_root),
        )
        return UnifiedGovernedRuntime(bridge=bridge, runtime_dir=temp_root)

    def setUp(self):
        self._temp_roots: list[Path] = []
        self.original_module_governance_runtime_dir = module_governance.runtime_dir
        self.runtime = self._make_runtime()

    def tearDown(self):
        module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        module_governance.reset()
        reset_registry()
        for temp_root in self._temp_roots:
            shutil.rmtree(temp_root, ignore_errors=True)

    def test_handle_request_is_deterministic_for_same_question(self):
        request = {
            "question": "What likely caused the runtime latency spike?",
            "intent": "diagnose_runtime",
            "tenant_id": "default",
            "context": {"component": "orchestrator"},
            "lane_types": ["symbolic", "graph", "llm"],
        }
        first = self._make_runtime().handle_request(request)
        second = self._make_runtime().handle_request(request)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(second["status"], "ok")

        def belief_signature(beliefs):
            return sorted(
                (
                    item.get("subject"),
                    item.get("predicate"),
                    item.get("object"),
                    item.get("status"),
                )
                for item in beliefs
            )

        self.assertEqual(
            belief_signature(first["convergence"]["final_beliefs"]),
            belief_signature(second["convergence"]["final_beliefs"]),
        )
        self.assertTrue(first["trace_id"])
        self.assertTrue(first["lane_results"])

    def test_blocked_when_bridge_rejects_detached_execution(self):
        result = self.runtime.handle_request(
            {
                "question": "run outside aa is",
                "intent": "general_qa",
                "context": {"standalone_jarvis": True, "bridge_bypass": True},
            }
        )
        self.assertIn(result["status"], {"blocked", "ok"})
        if result["bridge"].get("decision") == DECISION_BLOCK:
            self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
