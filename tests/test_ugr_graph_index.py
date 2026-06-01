"""Tests for UGR graph index v1."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.ugr.graph_index.index import GraphClaimIndex
from src.ugr.graph_index.store import GraphIndexStore, graph_index_enabled
from src.ugr.graph_index.sync import discover_claim_paths, load_claims_from_paths
from src.ugr.pattern_ledger import PatternLedgerStore
from src.ugr.unified_pattern_ledger import UnifiedPatternLedger


class TestGraphClaimIndex(unittest.TestCase):
    def setUp(self):
        self.index = GraphClaimIndex()
        self.claims = [
            {
                "record_type": "claim",
                "claim_id": "claim-global-1",
                "subject": "runtime orchestrator",
                "predicate": "latency_spike",
                "object": "observed after deploy",
                "tenant_scope": "global",
                "confidence": 0.8,
            },
            {
                "record_type": "claim",
                "claim_id": "claim-acme-1",
                "subject": "runtime orchestrator",
                "predicate": "tenant_config",
                "object": "acme override",
                "tenant_scope": "tenant:acme",
                "confidence": 0.7,
            },
            {
                "record_type": "claim",
                "claim_id": "claim-contoso-1",
                "subject": "secret workload",
                "predicate": "latency_spike",
                "object": "contoso only",
                "tenant_scope": "tenant:contoso",
                "confidence": 0.6,
            },
        ]
        self.index.rebuild(self.claims)

    def test_query_related_finds_global_claim(self):
        matches = self.index.query_related(["orchestrator"], tenant_scope="global")
        self.assertTrue(any(row["claim_id"] == "claim-global-1" for row in matches))

    def test_tenant_isolation_in_index_queries(self):
        matches = self.index.query_related(["orchestrator"], tenant_scope="tenant:acme")
        claim_ids = {row["claim_id"] for row in matches}
        self.assertIn("claim-global-1", claim_ids)
        self.assertIn("claim-acme-1", claim_ids)
        self.assertNotIn("claim-contoso-1", claim_ids)

    def test_subject_predicate_edge_lookup(self):
        matches = self.index.related_by_subject_predicate(
            "runtime orchestrator",
            "latency_spike",
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["claim_id"], "claim-global-1")


class TestGraphIndexStoreParity(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-graph-index-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        self.ledger = UnifiedPatternLedger(runtime_root=self.temp_root)
        for claim in (
            {
                "claim_id": "claim-1",
                "subject": "runtime orchestrator",
                "predicate": "latency_spike",
                "object": "observed after deploy",
                "tenant_scope": "global",
                "confidence": 0.8,
                "source_lane": "graph",
                "status": "accepted",
            },
            {
                "claim_id": "claim-2",
                "subject": "api gateway",
                "predicate": "error_rate",
                "object": "elevated",
                "tenant_scope": "global",
                "confidence": 0.7,
                "source_lane": "graph",
                "status": "accepted",
            },
        ):
            self.ledger.append_claim(claim, origin="test")

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_GRAPH_ENABLED", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_index_query_matches_jsonl_scan(self):
        graph = GraphIndexStore(runtime_root=self.temp_root, ledger=self.ledger)
        terms = ["orchestrator", "latency"]
        indexed = graph.query_related(terms, limit=10)
        scanned = graph.scan_query_related(terms, limit=10)
        self.assertEqual([row.get("claim_id") for row in indexed], [row.get("claim_id") for row in scanned])

    def test_rebuild_loads_discovered_claim_paths(self):
        paths = discover_claim_paths(self.temp_root)
        self.assertTrue(paths)
        graph = GraphIndexStore(runtime_root=self.temp_root, ledger=self.ledger)
        stats = graph.rebuild()
        self.assertGreaterEqual(stats["loaded_claims"], 2)
        self.assertGreaterEqual(graph.stats()["claim_count"], 2)


class TestPatternLedgerGraphSwitch(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-graph-switch-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_GRAPH_ENABLED", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _seed_claim(self, store: PatternLedgerStore) -> None:
        store.append_claim(
            {
                "claim_id": "claim-graph-1",
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

    def test_graph_enabled_uses_index_for_query_related(self):
        os.environ["UGR_GRAPH_ENABLED"] = "1"
        self.assertTrue(graph_index_enabled())
        store = PatternLedgerStore(runtime_dir=self.temp_root)
        self._seed_claim(store)
        self.assertIsNotNone(store._graph)
        matches = store.query_related(["orchestrator"], limit=5)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["claim_id"], "claim-graph-1")

    def test_graph_disabled_uses_jsonl_scan(self):
        os.environ["UGR_GRAPH_ENABLED"] = "0"
        store = PatternLedgerStore(runtime_dir=self.temp_root)
        self._seed_claim(store)
        self.assertIsNone(store._graph)
        matches = store.query_related(["orchestrator"], limit=5)
        self.assertEqual(len(matches), 1)

    def test_append_updates_graph_index_incrementally(self):
        os.environ["UGR_GRAPH_ENABLED"] = "1"
        store = PatternLedgerStore(runtime_dir=self.temp_root)
        self._seed_claim(store)
        store.append_claim(
            {
                "claim_id": "claim-graph-2",
                "subject": "api gateway",
                "predicate": "error_rate",
                "object": "elevated",
                "confidence": 0.7,
                "source_lane": "graph",
                "evidence_refs": [],
                "tenant_scope": "global",
                "status": "accepted",
            }
        )
        matches = store.query_related(["gateway"], limit=5)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["claim_id"], "claim-graph-2")


class TestGraphIndexManifestValidator(unittest.TestCase):
    def test_validator_passes(self):
        completed = subprocess.run(
            [sys.executable, "wolf-cog-os/scripts/validate-ugr-graph-index-manifest.py", "--mode", "fail"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
