"""Tests for UGR causal graph v1 and embryo v1 gateway."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.ugr.causal_graph.provenance import materialize_causal_edges
from src.ugr.causal_graph.region_health import RegionHealthRegistry
from src.ugr.causal_graph.store import CausalGraphStore, causal_graph_enabled
from src.ugr.embryo.gateway_v1 import UGREmbryoGatewayV1
from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.unified_pattern_ledger import UnifiedPatternLedger


class TestMaterializeCausalEdges(unittest.TestCase):
    def test_provenance_and_evidence_refs(self):
        claims = [
            {
                "claim_id": "claim-a",
                "subject": "deploy",
                "predicate": "caused",
                "object": "latency spike",
                "tenant_scope": "global",
                "confidence": 0.8,
                "evidence_refs": ["evidence-log-1"],
            },
            {
                "claim_id": "claim-b",
                "subject": "latency spike",
                "predicate": "observed",
                "object": "after rollout",
                "tenant_scope": "global",
                "confidence": 0.7,
            },
        ]
        links = [
            {
                "record_type": "provenance_link",
                "provenance_id": "prov-1",
                "node_or_edge_id": "claim-a",
                "evidence_id": "evidence-prov-1",
                "support_type": "supports",
                "weight": 0.9,
            }
        ]
        edges = materialize_causal_edges(claims=claims, provenance_links=links)
        edge_types = {edge["edge_type"] for edge in edges}
        self.assertIn("evidences", edge_types)
        self.assertIn("caused_by", edge_types)


class TestRegionHealthRegistry(unittest.TestCase):
    def test_resolve_region_for_tenant(self):
        registry = RegionHealthRegistry(config_path=Path("deploy/ugr/regions.json"))
        region_id = registry.resolve_region_for_tenant("tenant:acme")
        self.assertEqual(region_id, "tenant-us")
        snapshot = registry.health_snapshot()
        self.assertGreaterEqual(snapshot["region_count"], 2)


class TestCausalGraphStore(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-causal-graph-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["UGR_CAUSAL_GRAPH_ENABLED"] = "1"
        self.ledger = UnifiedPatternLedger(runtime_root=self.temp_root)
        claim_a = self.ledger.append_claim(
            {
                "claim_id": "claim-causal-a",
                "subject": "deploy pipeline",
                "predicate": "triggered",
                "object": "orchestrator restart",
                "tenant_scope": "global",
                "confidence": 0.8,
                "evidence_refs": ["evidence-causal-1"],
            },
            origin="test",
        )
        claim_b = self.ledger.append_claim(
            {
                "claim_id": "claim-causal-b",
                "subject": "orchestrator restart",
                "predicate": "caused",
                "object": "latency spike",
                "tenant_scope": "global",
                "confidence": 0.75,
            },
            origin="test",
        )
        self.ledger.append_provenance_link(
            node_or_edge_id=claim_a["claim_id"],
            evidence_id="evidence-prov-causal",
            support_type="supports",
            weight=0.85,
        )
        self._claim_a = claim_a
        self._claim_b = claim_b
        self.store = CausalGraphStore(runtime_root=self.temp_root, ledger=self.ledger)

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_CAUSAL_GRAPH_ENABLED", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_persistent_edge_log_created(self):
        self.assertTrue(self.store.edges_path.exists())
        lines = self.store.edges_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreater(len(lines), 0)
        first = json.loads(lines[0])
        self.assertEqual(first.get("graph_version"), "1.0")

    def test_query_causal_walk(self):
        result = self.store.query_causal(self._claim_a["claim_id"], depth=2)
        self.assertEqual(result["claim_id"], self._claim_a["claim_id"])
        self.assertTrue(result["edges"])
        edge_targets = {edge.get("to_id") for edge in result["edges"]}
        self.assertTrue({"evidence-causal-1", self._claim_b["claim_id"]} & edge_targets)

    def test_query_provenance(self):
        edges = self.store.query_provenance(self._claim_a["claim_id"])
        self.assertTrue(any(edge.get("source") == "provenance_link" for edge in edges))

    def test_region_health_snapshot(self):
        snapshot = self.store.region_health()
        self.assertIn("regions", snapshot)
        self.assertGreaterEqual(snapshot["healthy_regions"], 1)


class TestPatternLedgerCausalIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-causal-ledger-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["UGR_CAUSAL_GRAPH_ENABLED"] = "1"
        self.store = PatternLedgerStore(runtime_dir=self.temp_root)

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_CAUSAL_GRAPH_ENABLED", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_causal_graph_enabled_flag(self):
        self.assertTrue(causal_graph_enabled())
        stats = self.store.graph_index_stats()
        self.assertIsNotNone(stats)
        self.assertEqual(stats.get("graph_version"), "1.0")


class TestEmbryoGatewayV1(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-embryo-v1-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["UGR_CAUSAL_GRAPH_ENABLED"] = "1"
        from src.ugr.unified_runtime import UnifiedGovernedRuntime

        self.runtime = UnifiedGovernedRuntime(runtime_dir=self.temp_root)
        self.gateway = UGREmbryoGatewayV1(runtime=self.runtime)
        ledger = self.runtime.ledger
        record = ledger.append_claim(
            {
                "claim_id": ledger.make_claim_id("service mesh", "latency", "spike", "test"),
                "subject": "service mesh",
                "predicate": "latency",
                "object": "spike",
                "confidence": 0.8,
                "source_lane": "test",
                "evidence_refs": ["evidence-mesh-1"],
                "tenant_scope": "global",
                "status": "accepted",
            }
        )
        self.claim_id = record["claim_id"]

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_CAUSAL_GRAPH_ENABLED", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_v1_health_surface(self):
        payload = self.gateway.health()
        embryo = payload.get("embryo") or {}
        self.assertEqual(embryo.get("gateway_surface"), "v1")
        self.assertTrue(embryo.get("causal_graph_enabled"))

    def test_provenance_query(self):
        result = self.gateway.provenance_query(claim_id=self.claim_id)
        self.assertEqual(result.get("status"), "ok")
        self.assertTrue(result.get("edges"))

    def test_regions_health(self):
        result = self.gateway.regions_health()
        self.assertEqual(result.get("status"), "ok")
        self.assertIn("regions", result)


class TestCausalGraphManifestGate(unittest.TestCase):
    def test_manifest_validator_passes(self):
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / "wolf-cog-os" / "scripts" / "validate-ugr-causal-graph-manifest.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--repo-root", str(repo_root), "--mode", "fail"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
