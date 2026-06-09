"""Tests for UGR cloud super-LLM embryo v0."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.cognitive_bridge import CognitiveBridgeService
from src.immune_system import ImmuneSystemController
from src.jarvis_detachment_guard import JarvisDetachmentGuard
from src.module_governance import module_governance
from src.phase_gate import reset_registry
from src.ugr.embryo.gateway import UGREmbryoGateway
from src.ugr.embryo.health import probe_embryo_health
from src.ugr.embryo.model_pool import ModelPoolRouter, attach_model_pool_to_response
from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.unified_runtime import UnifiedGovernedRuntime


class TestModelPoolRouter(unittest.TestCase):
    def test_safe_rail_caps_tier(self):
        router = ModelPoolRouter()
        slot = router.resolve(
            request={"tenant_id": "default", "intent": "general_qa", "context": {}},
            trace_id="trace-pool-1",
            cloud_forge={
                "rail_decision": {"rail": "SAFE"},
                "cognition_plan": {"model_tier": "big"},
            },
            lane_results=[],
        )
        self.assertEqual(slot["rail"], "SAFE")
        self.assertIn(slot["selected_tier"], {"tiny", "mid"})
        self.assertTrue(slot["proposal_only"])
        self.assertEqual(slot["execution_authority"], "none")
        self.assertEqual(float(slot["generation_overrides"]["temperature"]), 0.0)

    def test_governed_llm_status_from_lane(self):
        router = ModelPoolRouter()
        slot = router.resolve(
            request={"tenant_id": "default"},
            trace_id="trace-pool-2",
            cloud_forge={"rail_decision": {"rail": "NORMAL"}, "cognition_plan": {"model_tier": "mid"}},
            lane_results=[
                {
                    "lane_type": "llm",
                    "payload": {
                        "governed_llm": {
                            "status": "PROPOSED",
                            "reason": "bounded_provider_proposal_ready",
                            "provider_request": {"provider": "local", "route_id": "think_local"},
                        }
                    },
                }
            ],
        )
        self.assertEqual(slot["governed_llm_status"], "PROPOSED")
        self.assertEqual(slot["provider"], "local")


class TestEmbryoGateway(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-embryo-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        module_governance.configure_runtime_dir(self.temp_root)
        module_governance.reset()
        reset_registry()
        bridge = CognitiveBridgeService(
            immune_controller=ImmuneSystemController(runtime_dir=self.temp_root),
            detachment_guard=JarvisDetachmentGuard(runtime_dir=self.temp_root),
        )
        runtime = UnifiedGovernedRuntime(bridge=bridge, runtime_dir=self.temp_root)
        self.gateway = UGREmbryoGateway(runtime=runtime)

    def tearDown(self):
        module_governance.configure_runtime_dir(Path(__file__).resolve().parents[1] / ".runtime")
        module_governance.reset()
        reset_registry()
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_deliberate_returns_embryo_envelope(self):
        result = self.gateway.deliberate(
            {
                "question": "What likely caused the runtime latency spike?",
                "intent": "diagnose_runtime",
                "lane_types": ["symbolic", "llm"],
            }
        )
        self.assertIn("embryo", result)
        self.assertEqual(result["embryo"]["gateway_surface"], "v0")
        self.assertIn("model_pool", result)
        self.assertIn("rail_decision", result)
        self.assertIn("trace_id", result)

    def test_health_reports_components(self):
        health = self.gateway.health()
        components = health["embryo"]["component_health"]
        self.assertIn("orchestrator", components)
        self.assertIn("model_pool", components)
        self.assertIn("immune", components)

    def test_graph_query_via_gateway(self):
        os.environ["UGR_GRAPH_ENABLED"] = "1"
        ledger = self.gateway.runtime.ledger
        ledger.append_claim(
            {
                "claim_id": "claim-embryo-1",
                "subject": "runtime orchestrator",
                "predicate": "latency_spike",
                "object": "observed after deploy",
                "confidence": 0.8,
                "source_lane": "graph",
                "evidence_refs": [],
                "tenant_scope": "global",
                "status": "accepted",
            }
        )
        result = self.gateway.graph_query(terms=["orchestrator"], limit=5)
        self.assertEqual(result["embryo"]["operation"], "graph_query")
        self.assertGreaterEqual(len(result.get("matches") or []), 1)
        os.environ.pop("UGR_GRAPH_ENABLED", None)


class TestEmbryoManifestValidator(unittest.TestCase):
    def test_validator_retired_without_wolf_forge(self):
        script = Path(__file__).resolve().parents[1] / "wolf-cog-os" / "scripts" / "validate-ugr-embryo-manifest.py"
        if not script.is_file():
            self.skipTest("wolf-cog-os UGR embryo manifest validator removed")
        completed = subprocess.run(
            [sys.executable, str(script), "--mode", "fail"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)


class TestRuntimeModelPoolAttachment(unittest.TestCase):
    def test_attach_model_pool_to_response(self):
        response = {
            "trace_id": "trace-attach-1",
            "lane_results": [],
            "cloud_forge": {"rail_decision": {"rail": "NORMAL"}, "cognition_plan": {"model_tier": "mid"}},
            "bridge": {"decision": "ALLOW"},
        }
        updated = attach_model_pool_to_response(response, {"tenant_id": "default"})
        self.assertIn("model_pool", updated)
        self.assertEqual(updated["model_pool"]["selected_tier"], "mid")


if __name__ == "__main__":
    unittest.main()
