"""Tests for unified pattern ledger v0.5."""

import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.unified_pattern_ledger import (
    UnifiedPatternLedger,
    normalize_cogos_pattern_record,
    normalize_detachment_pattern_event,
)


class TestUnifiedPatternLedger(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="unified-ledger-"))
        self.ledger = UnifiedPatternLedger(runtime_root=self.temp_root)

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_append_claim_writes_v05_record(self):
        record = self.ledger.append_claim(
            {
                "claim_id": "claim-test-1",
                "subject": "runtime orchestrator",
                "predicate": "latency_spike",
                "object": "after deploy",
                "confidence": 0.82,
                "source_lane": "graph",
                "status": "accepted",
                "evidence_refs": ["evidence-abc123"],
            }
        )
        self.assertEqual(record["record_type"], "claim")
        self.assertEqual(record["ledger_version"], "0.5")
        self.assertTrue(self.ledger.claims_path.exists())

    def test_detachment_event_mirrors_legacy_path(self):
        entry = {
            "event_id": "cpl_test123",
            "timestamp": "2026-05-28T12:00:00+00:00",
            "type": "detachment_attempt",
            "vector": "external_launch",
            "decision": "blocked",
            "severity": "S3",
            "runtime_context": "live_runtime",
            "packet_type": "operator_turn",
            "source_class": "chat_session",
            "signature_only": True,
        }
        self.ledger.append_pattern_event(entry, mirror_legacy=True)
        self.assertTrue(self.ledger.legacy_detachment_path.exists())
        self.assertTrue(self.ledger._path_for("pattern_event").exists())

    def test_tenant_scoped_query_does_not_leak(self):
        self.ledger.append_claim(
            {
                "claim_id": "claim-global",
                "subject": "shared service",
                "predicate": "status",
                "object": "healthy",
                "confidence": 0.9,
                "source_lane": "graph",
                "status": "accepted",
                "tenant_scope": "global",
            }
        )
        self.ledger.append_claim(
            {
                "claim_id": "claim-tenant-a",
                "subject": "shared service",
                "predicate": "status",
                "object": "private",
                "confidence": 0.9,
                "source_lane": "graph",
                "status": "accepted",
                "tenant_scope": "tenant:a",
            }
        )
        tenant_rows = self.ledger.read_claims(tenant_scope="tenant:a")
        self.assertEqual(len(tenant_rows), 1)
        self.assertEqual(tenant_rows[0]["tenant_scope"], "tenant:a")

    def test_cogos_adapter_normalizes_pattern_event(self):
        normalized = normalize_cogos_pattern_record(
            {
                "pattern_id": "pat-1",
                "classification": "failure",
                "severity": "S4",
                "subject": "module_x",
                "summary": "trait drift",
                "source": "trait_drift",
            }
        )
        self.assertEqual(normalized["record_type"], "pattern_event")
        self.assertEqual(normalized["origin"], "cogos")
        self.assertEqual(normalized["classification"], "failure")

    def test_detachment_adapter_normalizes_pattern_event(self):
        normalized = normalize_detachment_pattern_event(
            {"type": "detachment_attempt", "decision": "blocked", "severity": "S3"}
        )
        self.assertEqual(normalized["origin"], "detachment_guard")
        self.assertEqual(normalized["classification"], "near_miss")


if __name__ == "__main__":
    unittest.main()
