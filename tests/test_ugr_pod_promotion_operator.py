"""Tests for POD proven path operator knowledge promotion hook."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ugr.discovery.discovery_pod_ledger import upgrade_pod_on_discovery


def _proven_receipt(contribution_id: str = "contrib-pod-proven") -> dict:
    return {
        "contribution_id": contribution_id,
        "contribution_type": "proof",
        "operator_id": "operator:ada",
        "receipt_sig": "sig-test",
        "payload": {
            "claim_label": "proven",
            "title": "Pod proven contribution",
            "proof_path": "proofs/pod.json",
            "discovery_pod_id": "pod:ada-lovelace",
            "pod_display_name": "Ada Lovelace",
        },
        "proof": {"title": "Pod proven contribution"},
        "verification": {"artifacts": ["artifact-1"]},
    }


class TestUgrPodPromotionOperator(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="urg-pod-promo-"))
        self.ledger_path = self.temp_root / "discovery-pods.jsonl"
        self.registry_path = self.temp_root / "discovery-pods.json"

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    @patch("src.urg_operator_knowledge_bridge.promote_from_receipt")
    def test_upgrade_pod_on_discovery_promotes_proven_receipt(self, promote_mock):
        promote_mock.return_value = {
            "ok": True,
            "promoted": True,
            "contribution_id": "contrib-pod-proven",
        }
        receipt = _proven_receipt()
        result = upgrade_pod_on_discovery(
            operator_id="operator:ada",
            tenant_id="global",
            contribution_id=receipt["contribution_id"],
            contribution_type="proof",
            spec_payload=dict(receipt["payload"]),
            receipt=receipt,
            ledger_path=self.ledger_path,
            registry_path=self.registry_path,
        )
        self.assertIn("pod_proven", result)
        self.assertIn("operator_knowledge_promotion", result)
        promote_mock.assert_called_once()
        self.assertTrue(self.ledger_path.exists())
        rows = [json.loads(line) for line in self.ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        event_types = {row.get("event_type") for row in rows}
        self.assertIn("pod_proven", event_types)


if __name__ == "__main__":
    unittest.main()
