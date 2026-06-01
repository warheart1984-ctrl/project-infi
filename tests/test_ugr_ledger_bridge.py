"""UGR Ledger Bridge v1 tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.ugr.ledger_bridge.bridge import LedgerBridge, LedgerClaim
from src.ugr.ledger_bridge.invariants import BridgeInvariantError, validate_bridge_invariants


class _FakeTrustOrgan:
    def receive_claim(self, claim: dict, *, bridge_trace: dict | None = None) -> dict:
        return {
            "receipt_id": "fake-receipt",
            "acknowledged": True,
            "claim_id": claim.get("claim_id"),
        }


class TestBridgeInvariants(unittest.TestCase):
    def test_blocks_missing_sigil(self):
        with self.assertRaises(BridgeInvariantError) as ctx:
            validate_bridge_invariants(
                claim={"claim_id": "c1", "law_id": "law-a", "law_version": "1.0"},
                lane="NORMAL",
                session_id="s1",
                law_id="law-a",
                law_version="1.0",
            )
        self.assertEqual(ctx.exception.code, "GOV-03")

    def test_express_requires_clearance(self):
        with self.assertRaises(BridgeInvariantError) as ctx:
            validate_bridge_invariants(
                claim={
                    "claim_id": "c2",
                    "law_id": "law-a",
                    "law_version": "1.0",
                    "sigil": "sig-1",
                    "source_node": "n1",
                },
                lane="EXPRESS",
                session_id="s1",
                law_id="law-a",
                law_version="1.0",
            )
        self.assertEqual(ctx.exception.code, "GOV-06")


class TestLedgerBridgeTraverse(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="bridge-"))
        self.organ = _FakeTrustOrgan()
        self.bridge = LedgerBridge(
            trust_organ=self.organ,
            trace_path=self.temp / "bridge_trace.jsonl",
        )

    def test_traverse_elevates_to_proven(self):
        claim = LedgerClaim(
            claim_id="claim-1",
            law_id="law-pilot",
            law_version="1.0.0",
            sigil="operator-sigil",
            source_node="node-abc",
            human_explicit=True,
        )
        result = self.bridge.traverse(
            claim,
            lane="NORMAL",
            session_id="sess-1",
            law_id="law-pilot",
            law_version="1.0.0",
        )
        self.assertEqual(result.claim_label, "proven")
        self.assertEqual(result.status, "elevated")
        trace = self.bridge.query_trace("claim-1")
        self.assertGreaterEqual(len(trace), 2)

    def test_runner_only_blocked_on_duplicate(self):
        claim = LedgerClaim(
            claim_id="claim-dup",
            law_id="law-pilot",
            law_version="1.0.0",
            sigil="sig",
            source_node="n1",
        )
        self.bridge.traverse(claim, lane="NORMAL", session_id="s", law_id="law-pilot", law_version="1.0.0")
        second = self.bridge.traverse(claim, lane="NORMAL", session_id="s", law_id="law-pilot", law_version="1.0.0")
        self.assertEqual(second.status, "blocked")


if __name__ == "__main__":
    unittest.main()
