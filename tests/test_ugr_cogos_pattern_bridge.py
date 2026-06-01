"""Tests for Wolf CoG → unified ledger write-path bridge (UGR-D4)."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.cogos_pattern_bridge import CogosPatternBridge
from src.ugr.pattern_ledger import PatternLedgerStore


COGOS_FIXTURE_ROW = {
    "pattern_id": "pattern-cogos-test-1",
    "timestamp": "2026-05-28T12:00:00+00:00",
    "source": "module_execution",
    "event": "pattern.classified",
    "classification": "failure",
    "severity": "S2",
    "subject": "runtime orchestrator",
    "summary": "Sandbox denial during module execution",
    "signature": "sig-test-1",
    "status": "accepted",
}


class TestCogosPatternBridge(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-cogos-bridge-"))
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        self.ledger = PatternLedgerStore(runtime_dir=self.temp_root)
        self.bridge = CogosPatternBridge(ledger=self.ledger, runtime_root=self.temp_root)

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_ingest_writes_unified_pattern_event(self):
        result = self.bridge.ingest_record(COGOS_FIXTURE_ROW)
        self.assertTrue(result.get("written"))
        events_path = self.ledger.events_path
        self.assertTrue(events_path.exists())
        rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("origin"), "cogos")
        self.assertEqual(rows[0].get("pattern_id"), "pattern-cogos-test-1")

    def test_duplicate_pattern_id_is_idempotent(self):
        first = self.bridge.ingest_record(COGOS_FIXTURE_ROW)
        second = self.bridge.ingest_record(COGOS_FIXTURE_ROW)
        self.assertTrue(first.get("written"))
        self.assertFalse(second.get("written"))
        self.assertEqual(second.get("status"), "duplicate")
        rows = [json.loads(line) for line in self.ledger.events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(rows), 1)

    def test_pattern_ledger_sync_fixture_rows(self):
        stats = self.ledger.sync_cogos_patterns(rows=[COGOS_FIXTURE_ROW])
        self.assertEqual(stats.get("ingested"), 1)
        self.assertTrue(self.ledger.events_path.exists())


if __name__ == "__main__":
    unittest.main()
