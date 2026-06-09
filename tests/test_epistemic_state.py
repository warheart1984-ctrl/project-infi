"""Tests for canonical 3-state epistemic layer over 4-band Standing."""

from __future__ import annotations

import unittest

from src.ugr.discovery.proof_promotion import rejection_source_for_rule
from src.ugr.discovery.standing import (
    EpistemicState,
    Standing,
    build_epistemic_envelope,
    enrich_payload_with_standing,
    epistemic_from_receipt,
    epistemic_from_standing,
    is_immutable_epistemic,
    is_library_admitted_epistemic,
    is_operator_promotable,
    standing_from_epistemic,
    standing_from_receipt,
)


class TestEpistemicMapping(unittest.TestCase):
    def test_four_band_to_three_state(self):
        self.assertEqual(epistemic_from_standing(Standing.DENIED), EpistemicState.REJECTED)
        self.assertEqual(epistemic_from_standing(Standing.HYPOTHETICAL), EpistemicState.PENDING)
        self.assertEqual(epistemic_from_standing(Standing.ASSERTED), EpistemicState.PENDING)
        self.assertEqual(epistemic_from_standing(Standing.PROVEN), EpistemicState.PROVEN)

    def test_rejection_source_forces_rejected(self):
        self.assertEqual(
            epistemic_from_standing(Standing.ASSERTED, rejection_source="discovery_denial"),
            EpistemicState.REJECTED,
        )

    def test_rejected_label_forces_rejected(self):
        self.assertEqual(
            epistemic_from_standing(Standing.HYPOTHETICAL, claim_label="rejected"),
            EpistemicState.REJECTED,
        )

    def test_three_state_to_four_band(self):
        self.assertEqual(standing_from_epistemic(EpistemicState.REJECTED), Standing.DENIED)
        self.assertEqual(standing_from_epistemic(EpistemicState.PENDING), Standing.ASSERTED)
        self.assertEqual(standing_from_epistemic(EpistemicState.PROVEN), Standing.PROVEN)

    def test_promotion_guards(self):
        self.assertTrue(is_operator_promotable(EpistemicState.PROVEN))
        self.assertFalse(is_operator_promotable(EpistemicState.PENDING))
        self.assertFalse(is_operator_promotable(EpistemicState.REJECTED))
        self.assertTrue(is_library_admitted_epistemic(EpistemicState.PENDING))
        self.assertFalse(is_library_admitted_epistemic(EpistemicState.REJECTED))
        self.assertTrue(is_immutable_epistemic(EpistemicState.REJECTED))
        self.assertTrue(is_immutable_epistemic(EpistemicState.PROVEN))
        self.assertFalse(is_immutable_epistemic(EpistemicState.PENDING))


class TestEpistemicEnvelope(unittest.TestCase):
    def test_build_envelope(self):
        envelope = build_epistemic_envelope(
            Standing.PROVEN,
            contribution_id="cid-1",
            pod_id="pod-1",
        )
        self.assertEqual(envelope["epistemic_state"], "proven")
        self.assertEqual(envelope["standing"], 3)
        self.assertEqual(envelope["claim_label"], "proven")
        self.assertEqual(envelope["contribution_id"], "cid-1")
        self.assertEqual(envelope["pod_id"], "pod-1")

    def test_enrich_payload(self):
        payload = enrich_payload_with_standing(
            {"proof_path": "proofs/x.json"},
            standing=Standing.DENIED,
            claim_label="denied",
            rejection_source="discovery_denial",
            falsity_fingerprint="fp-abc",
        )
        self.assertEqual(payload["epistemic_state"], "rejected")
        self.assertEqual(payload["rejection_source"], "discovery_denial")
        self.assertEqual(payload["falsity_fingerprint"], "fp-abc")

    def test_epistemic_from_receipt(self):
        receipt = {
            "payload": {
                "standing": 3,
                "claim_label": "proven",
                "epistemic_state": "proven",
            }
        }
        self.assertEqual(epistemic_from_receipt(receipt), EpistemicState.PROVEN)
        self.assertEqual(standing_from_receipt(receipt), Standing.PROVEN)

    def test_rejection_source_for_deny_rules(self):
        self.assertEqual(rejection_source_for_rule("deny:grant"), "discovery_denial")
        self.assertIsNone(rejection_source_for_rule("verify:ci"))


if __name__ == "__main__":
    unittest.main()
