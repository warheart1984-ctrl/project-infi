"""Tests for URG operator knowledge bridge."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.urg_operator_knowledge_bridge import (
    build_urg_library_context,
    is_already_promoted,
    load_urg_library_snapshot,
    promote_from_receipt,
)
from src.ugr.discovery.contribution_store import ContributionDiscoveryStore


def _proven_receipt(contribution_id: str = "contrib-proven-1") -> dict:
    return {
        "contribution_id": contribution_id,
        "contribution_type": "proof",
        "operator_id": "operator:test",
        "receipt_verified": True,
        "payload": {
            "claim_label": "proven",
            "title": "Test proven claim",
            "proof_path": "proofs/test.json",
        },
        "proof": {"title": "Test proven claim"},
    }


def _pending_receipt(contribution_id: str = "contrib-pending-1") -> dict:
    return {
        "contribution_id": contribution_id,
        "contribution_type": "proof",
        "operator_id": "operator:test",
        "payload": {
            "claim_label": "asserted",
            "title": "Pending claim",
        },
    }


class TestUrgOperatorKnowledgeBridge(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="urg-bridge-"))
        self.store = ContributionDiscoveryStore(runtime_dir=self.temp_root, tenant_id="global")

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _seed_catalog(self, receipt: dict) -> None:
        cid = receipt["contribution_id"]
        row = {
            "contribution_id": cid,
            "contribution_type": receipt.get("contribution_type"),
            "operator_id": receipt.get("operator_id"),
            "summary": receipt.get("payload", {}).get("title"),
            "receipt": receipt,
        }
        with self.store.discoveries_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        with self.store.catalog_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "contribution_id": cid,
                        "contribution_type": receipt.get("contribution_type"),
                        "operator_id": receipt.get("operator_id"),
                        "summary": receipt.get("payload", {}).get("title"),
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    def test_load_snapshot_includes_pending_and_proven(self):
        self._seed_catalog(_pending_receipt())
        self._seed_catalog(_proven_receipt())
        snapshot = load_urg_library_snapshot(runtime_dir=self.temp_root, limit=10)
        states = {row["epistemic_state"] for row in snapshot["entries"]}
        self.assertIn("pending", states)
        self.assertIn("proven", states)

    def test_build_context_includes_prompt_block(self):
        self._seed_catalog(_proven_receipt())
        context = build_urg_library_context(runtime_dir=self.temp_root, query="proven")
        self.assertGreaterEqual(context["entry_count"], 1)
        self.assertIn("URG library knowledge", context["prompt_block"])

    def test_promote_skips_non_proven(self):
        result = promote_from_receipt(
            _pending_receipt(),
            operator_id="operator:test",
            runtime_dir=self.temp_root,
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("reason"), "not_operator_promotable")

    def test_promote_proven_is_idempotent(self):
        memory = MagicMock()
        memory.add_memory.return_value = {"id": "mem-1"}
        first = promote_from_receipt(
            _proven_receipt(),
            operator_id="operator:test",
            runtime_dir=self.temp_root,
            memory_enforcer=memory,
            record_odl=False,
        )
        second = promote_from_receipt(
            _proven_receipt(),
            operator_id="operator:test",
            runtime_dir=self.temp_root,
            memory_enforcer=memory,
            record_odl=False,
        )
        self.assertTrue(first.get("promoted"))
        self.assertTrue(second.get("idempotent"))
        self.assertTrue(is_already_promoted("contrib-proven-1", runtime_dir=self.temp_root))
        memory.add_memory.assert_called_once()


if __name__ == "__main__":
    unittest.main()
