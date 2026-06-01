"""Tests for external graph query backend (SQLite projection)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.graph_backends.factory import create_query_backend, load_graph_backend_config
from src.ugr.graph_index.store import GraphIndexStore
from src.ugr.unified_pattern_ledger import UnifiedPatternLedger


class TestSQLiteGraphBackend(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-graph-backend-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["UGR_GRAPH_QUERY_BACKEND"] = "sqlite"
        self.ledger = UnifiedPatternLedger(runtime_root=self.temp_root)
        self.ledger.append_claim(
            {
                "claim_id": "claim-sqlite-1",
                "subject": "runtime orchestrator",
                "predicate": "latency_spike",
                "object": "observed after deploy",
                "tenant_scope": "global",
                "confidence": 0.8,
            },
            origin="test",
        )
        self.ledger.append_claim(
            {
                "claim_id": "claim-sqlite-acme",
                "subject": "runtime orchestrator",
                "predicate": "tenant_config",
                "object": "acme override",
                "tenant_scope": "tenant:acme",
                "confidence": 0.7,
            },
            origin="test",
        )

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_GRAPH_QUERY_BACKEND", None)
        os.environ.pop("UGR_GRAPH_ENABLED", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_sqlite_backend_parity_with_memory_index(self):
        os.environ["UGR_GRAPH_ENABLED"] = "1"
        store = GraphIndexStore(runtime_root=self.temp_root, ledger=self.ledger)
        memory_matches = store.index.query_related(["orchestrator"], tenant_scope="global")
        sqlite_matches = store.query_related(["orchestrator"], tenant_scope="global")
        memory_ids = {row["claim_id"] for row in memory_matches}
        sqlite_ids = {row["claim_id"] for row in sqlite_matches}
        self.assertIn("claim-sqlite-1", sqlite_ids)
        self.assertEqual(memory_ids, sqlite_ids)
        stats = store.stats()
        self.assertEqual(stats["query_backend"]["backend"], "sqlite")

    def test_graph_backend_config_documents_sqlite_choice(self):
        config = load_graph_backend_config()
        self.assertEqual(config.get("selected_external_db"), "sqlite")
        backend = create_query_backend(runtime_root=self.temp_root, config=config)
        self.assertIsNotNone(backend)
        rebuild_stats = backend.rebuild_from_canonical()
        self.assertGreaterEqual(rebuild_stats["claim_count"], 2)


if __name__ == "__main__":
    unittest.main()
