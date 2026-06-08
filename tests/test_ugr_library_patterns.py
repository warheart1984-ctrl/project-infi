"""Tests for library reference patterns and matcher rewards."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.contribution_spec import ContributionSpec, contribution_id_from_spec
from src.ugr.discovery.library_patterns import (
    is_library_reference_contribution,
    match_library_patterns,
    rewards_suppressed_for_receipt,
)
from src.ugr.discovery.standing import enrich_payload_with_standing


def _matching_proof_text() -> str:
    return """
    Multi-model orchestration pattern with role-separation across Model A and coding agents.
    Governance uses Voss Binding, OTEM, proof bundles, deny patterns, and promotion gates
    in a constitutional runtime. Parallel-processing lanes integrate the outputs from threads.
    Documentation-as-you-build with zero drift. Standing 2 asserted epistemic governance.
    """


class TestLibraryPatterns(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-lib-pattern-"))
        self.proof_dir = self.temp_root / "packets"
        self.proof_dir.mkdir(parents=True)
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "test-lib-pattern-key"
        os.environ["UGR_SUBSYSTEM_DISCOVERY_ENABLED"] = "1"
        os.environ["UGR_REWARDS_SHADOW_ONLY"] = "1"

    def tearDown(self):
        for key in (
            "AAIS_RUNTIME_DIR",
            "URG_RECEIPT_SIGNING_KEY",
            "UGR_SUBSYSTEM_DISCOVERY_ENABLED",
            "UGR_REWARDS_SHADOW_ONLY",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_match_library_patterns_hits_threshold(self):
        haystack = _matching_proof_text().lower()
        matches = match_library_patterns(haystack)
        ids = {m.get("pattern_id") for m in matches}
        self.assertIn("multi_model_orchestration", ids)

    def test_library_reference_flags(self):
        receipt = {
            "payload": {
                "kind": "library_pattern",
                "library_reference": True,
                "rewards_suppressed": True,
                "slug": "multi_model_orchestration_pattern",
            }
        }
        self.assertTrue(is_library_reference_contribution(receipt))
        self.assertTrue(rewards_suppressed_for_receipt(receipt))

    def test_reference_registration_suppresses_rewards(self):
        proof_path = self.proof_dir / "reference_proof.md"
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
        result = service.discover(
            {
                "tenant_id": "global",
                "operator_id": "operator:jon-halstead",
                "aais_instance_id": "aais-primary",
                "contribution_type": "proof",
                "payload": payload,
            }
        )
        self.assertEqual(result.get("status"), "discovered")
        rewards = result.get("operator_rewards") or {}
        self.assertEqual(rewards.get("status"), "suppressed")
        pattern_rewards = result.get("library_pattern_rewards") or {}
        self.assertEqual(pattern_rewards.get("status"), "skipped")

    def _discover_matching_proof(
        self,
        *,
        operator_id: str,
        slug: str,
        proof_filename: str,
    ) -> dict:
        proof_path = self.proof_dir / proof_filename
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
                "tenant_id": "global",
                "operator_id": operator_id,
                "aais_instance_id": "aais-primary",
                "contribution_type": "proof",
                "payload": payload,
            }
        )

    def _assert_matcher_matched(self, result: dict) -> None:
        self.assertEqual(result.get("status"), "discovered")
        rewards = result.get("operator_rewards") or {}
        self.assertNotEqual(rewards.get("status"), "suppressed")
        pattern_rewards = result.get("library_pattern_rewards") or {}
        self.assertEqual(pattern_rewards.get("status"), "matched")
        matches = pattern_rewards.get("matches") or []
        self.assertTrue(any(m.get("pattern_id") == "multi_model_orchestration" for m in matches))

    def test_matching_contribution_gets_matcher_rewards(self):
        result = self._discover_matching_proof(
            operator_id="operator:other",
            slug="some_future_orchestration_work",
            proof_filename="matching_proof.md",
        )
        self._assert_matcher_matched(result)

    def test_two_operators_both_get_matcher_rewards(self):
        first = self._discover_matching_proof(
            operator_id="operator:alice",
            slug="alice_orchestration_v1",
            proof_filename="alice_match.md",
        )
        second = self._discover_matching_proof(
            operator_id="operator:bob",
            slug="bob_orchestration_v1",
            proof_filename="bob_match.md",
        )
        self._assert_matcher_matched(first)
        self._assert_matcher_matched(second)
        self.assertNotEqual(first.get("contribution_id"), second.get("contribution_id"))

    def test_same_operator_repeat_matching_contributions(self):
        first = self._discover_matching_proof(
            operator_id="operator:repeat",
            slug="repeat_orchestration_alpha",
            proof_filename="repeat_alpha.md",
        )
        second = self._discover_matching_proof(
            operator_id="operator:repeat",
            slug="repeat_orchestration_beta",
            proof_filename="repeat_beta.md",
        )
        self._assert_matcher_matched(first)
        self._assert_matcher_matched(second)
        self.assertNotEqual(first.get("contribution_id"), second.get("contribution_id"))
        first_matches = (first.get("library_pattern_rewards") or {}).get("matches") or []
        second_matches = (second.get("library_pattern_rewards") or {}).get("matches") or []
        first_event = first_matches[0].get("event_id")
        second_event = second_matches[0].get("event_id")
        if first_event and second_event:
            self.assertNotEqual(first_event, second_event)

    def test_contribution_id_stable_for_library_pattern(self):
        payload = enrich_payload_with_standing(
            {
                "slug": "multi_model_orchestration_pattern",
                "kind": "library_pattern",
                "library_pattern_id": "multi_model_orchestration",
                "proof_path": "docs/proof/discovery/packets/MULTI_MODEL_ORCHESTRATION_PATTERN_DISCOVERY_PROOF.md",
            },
            standing=2,
            claim_label="asserted",
        )
        spec = ContributionSpec(contribution_type="proof", payload=payload)
        self.assertEqual(len(contribution_id_from_spec(spec)), 64)


if __name__ == "__main__":
    unittest.main()
