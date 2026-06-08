"""Chaos and edge-case tests for UGR reward ledger integrity."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.standing import enrich_payload_with_standing
from src.ugr.governance.ledger_inspection import inspect_ugr_ledger
from src.ugr.rewards.operator_reward_spec import EVENT_LIBRARY_PATTERN_MATCHED
from src.ugr.rewards.reward_issuer import issue_reward
from src.ugr.rewards.reward_ledger import RewardLedger


def _matching_proof_text() -> str:
    return """
    Multi-model orchestration pattern with role-separation across Model A and coding agents.
    Governance uses Voss Binding, OTEM, proof bundles, deny patterns, and promotion gates
    in a constitutional runtime. Parallel-processing lanes integrate the outputs from threads.
    Documentation-as-you-build with zero drift. Standing 2 asserted epistemic governance.
    """


class TestUgrLedgerChaos(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-ledger-chaos-"))
        self.proof_dir = self.temp_root / "packets"
        self.proof_dir.mkdir(parents=True)
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-ledger-chaos-key"
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "1"
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "0"

    def tearDown(self):
        for key in (
            "AAIS_RUNTIME_DIR",
            "URG_RECEIPT_SIGNING_KEY",
            "UGR_SUBSYSTEM_DISCOVERY_ENABLED",
            "UGR_REWARDS_SHADOW_ONLY",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _discover_matching(
        self,
        *,
        operator_id: str,
        slug: str,
        tenant_id: str = "global",
    ) -> dict:
        proof_path = self.proof_dir / f"{slug}.md"
        proof_path.write_text(_matching_proof_text(), encoding="utf-8")
        payload = enrich_payload_with_standing(
            {
                "proof_path": str(proof_path),
                "slug": slug,
                "title": slug.replace("_", " ").title(),
                "discovery_pod_id": f"pod:{operator_id.split(':', 1)[-1]}",
            },
            standing=2,
            claim_label="asserted",
        )
        service = ContributionDiscoveryService(runtime_dir=str(self.temp_root))
        return service.discover(
            {
                "tenant_id": tenant_id,
                "operator_id": operator_id,
                "aais_instance_id": "aais-primary",
                "contribution_type": "proof",
                "payload": payload,
            }
        )

    def test_idempotent_rediscovery_emits_matcher_rewards_once(self):
        first = self._discover_matching(
            operator_id="operator:chaos-idem",
            slug="chaos_idem_alpha",
        )
        second = self._discover_matching(
            operator_id="operator:chaos-idem",
            slug="chaos_idem_alpha",
        )
        self.assertTrue(second.get("idempotent"))
        pattern_rewards = second.get("library_pattern_rewards") or {}
        self.assertEqual(pattern_rewards.get("status"), "matched")

        ledger = RewardLedger(runtime_dir=str(self.temp_root), tenant_id="global")
        cid = first.get("contribution_id")
        events = [
            row
            for row in ledger._iter_rewards_rows()
            if str(row.get("contribution_id") or row.get("subsystem_id") or "") == cid
            and str(row.get("event_type") or "") == EVENT_LIBRARY_PATTERN_MATCHED
        ]
        self.assertEqual(len(events), 1)

    def test_duplicate_event_id_append_rejected(self):
        ledger = RewardLedger(runtime_dir=str(self.temp_root), tenant_id="global")
        event = {
            "event_id": "chaos-dup-event-001",
            "event_type": "test_event",
            "operator_id": "operator:chaos",
            "tenant_id": "global",
            "issued_at": 1.0,
            "deltas": {"reputation": 1.0},
        }
        self.assertTrue(ledger.append_event(event))
        self.assertFalse(ledger.append_event(event))

    def test_inspector_passes_after_matching_discovery(self):
        self._discover_matching(
            operator_id="operator:inspector",
            slug="inspector_match",
        )
        report = inspect_ugr_ledger(runtime_dir=str(self.temp_root), tenant_id="global")
        self.assertTrue(report.get("ok"), msg=json.dumps(report.get("issues"), indent=2))

    def test_cross_tenant_isolation(self):
        global_result = self._discover_matching(
            operator_id="operator:tenant-a",
            slug="tenant_a_proof",
            tenant_id="global",
        )
        other_result = self._discover_matching(
            operator_id="operator:tenant-b",
            slug="tenant_b_proof",
            tenant_id="tenant:other",
        )
        self.assertEqual(global_result.get("status"), "discovered")
        self.assertEqual(other_result.get("status"), "discovered")

        global_ledger = RewardLedger(runtime_dir=str(self.temp_root), tenant_id="global")
        other_ledger = RewardLedger(runtime_dir=str(self.temp_root), tenant_id="tenant:other")
        global_events = global_ledger._iter_rewards_rows()
        other_events = other_ledger._iter_rewards_rows()
        self.assertTrue(global_events)
        self.assertTrue(other_events)
        self.assertNotEqual(
            str(global_ledger.tenant_rewards_path),
            str(other_ledger.tenant_rewards_path),
        )

        global_report = inspect_ugr_ledger(runtime_dir=str(self.temp_root), tenant_id="global")
        other_report = inspect_ugr_ledger(runtime_dir=str(self.temp_root), tenant_id="tenant:other")
        self.assertTrue(global_report.get("ok"))
        self.assertTrue(other_report.get("ok"))

    def test_issue_reward_skip_if_exists_is_idempotent(self):
        first = issue_reward(
            tenant_id="global",
            operator_id="operator:issue-idem",
            contribution_id="contrib-chaos-001",
            event_type=EVENT_LIBRARY_PATTERN_MATCHED,
            discovery_receipt={"contribution_id": "contrib-chaos-001"},
            primary_anchor="multi_model_orchestration",
            secondary_anchor="contrib-chaos-001",
            runtime_dir=str(self.temp_root),
        )
        second = issue_reward(
            tenant_id="global",
            operator_id="operator:issue-idem",
            contribution_id="contrib-chaos-001",
            event_type=EVENT_LIBRARY_PATTERN_MATCHED,
            discovery_receipt={"contribution_id": "contrib-chaos-001"},
            primary_anchor="multi_model_orchestration",
            secondary_anchor="contrib-chaos-001",
            runtime_dir=str(self.temp_root),
        )
        self.assertNotEqual(first.get("status"), "skipped")
        self.assertEqual(second.get("status"), "idempotent")

        ledger = RewardLedger(runtime_dir=str(self.temp_root), tenant_id="global")
        matching = [
            row
            for row in ledger._iter_rewards_rows()
            if str(row.get("event_type") or "") == EVENT_LIBRARY_PATTERN_MATCHED
            and str(row.get("operator_id") or "") == "operator:issue-idem"
        ]
        self.assertEqual(len(matching), 1)

    def test_reference_contribution_skips_matcher_on_rediscovery(self):
        proof_path = self.proof_dir / "reference_rediscover.md"
        proof_path.write_text("# library reference\n", encoding="utf-8")
        payload = enrich_payload_with_standing(
            {
                "proof_path": str(proof_path),
                "slug": "multi_model_orchestration_pattern",
                "kind": "library_pattern",
                "library_reference": True,
                "rewards_suppressed": True,
                "library_pattern_id": "multi_model_orchestration",
                "discovery_pod_id": "pod:jon-halstead",
            },
            standing=2,
            claim_label="asserted",
        )
        service = ContributionDiscoveryService(runtime_dir=str(self.temp_root))
        request = {
            "tenant_id": "global",
            "operator_id": "operator:jon-halstead",
            "aais_instance_id": "aais-primary",
            "contribution_type": "proof",
            "payload": payload,
        }
        first = service.discover(request)
        second = service.discover(request)
        self.assertEqual((first.get("library_pattern_rewards") or {}).get("status"), "skipped")
        self.assertEqual((second.get("library_pattern_rewards") or {}).get("status"), "skipped")
        self.assertTrue(second.get("idempotent"))


if __name__ == "__main__":
    unittest.main()
