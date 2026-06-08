"""Tests for Library Standing resolution (discovery-proof-promotion v3)."""

import unittest

from src.ugr.discovery.proof_promotion import (
    load_promotion_policy,
    resolve_claim_label,
    resolve_standing,
    should_downgrade_claim_label,
    should_exclude_from_library,
    should_upgrade_claim_label,
)
from src.ugr.discovery.standing import Standing
from src.ugr.rewards.operator_profile import OperatorProfile
from src.ugr.rewards.operator_reward_spec import EVENT_PROOF_PACKET_PUBLISHED
from src.ugr.rewards.reward_calculator import compute_deltas


class TestProofPromotion(unittest.TestCase):
    def setUp(self):
        self.policy = load_promotion_policy()

    def test_formal_theory_is_hypothetical(self):
        label, rule = resolve_claim_label(
            {
                "title": "A Formal Theory of the Duality Invariant",
                "slug": "a_formal_theory_of_the_duality_invariant",
                "source_path": "A Formal Theory of the Duality Invariant.pdf",
            },
            policy=self.policy,
        )
        self.assertEqual(label, "hypothetical")
        self.assertTrue(rule and rule.startswith("hypothetical:"))

    def test_architecture_without_verification_is_asserted(self):
        label, rule = resolve_claim_label(
            {
                "title": "Hyper-Systemizer Formal Specification",
                "slug": "hyper_systemizer_formal_specification",
                "source_path": "Hyper-Systemizer Formal Specification.pdf",
            },
            policy=self.policy,
        )
        self.assertEqual(label, "asserted")
        self.assertTrue(rule and rule.startswith("asserted:"))

    def test_architecture_with_verification_is_proven(self):
        standing, label, rule = resolve_standing(
            {
                "title": "Hyper-Systemizer Formal Specification",
                "slug": "hyper_systemizer_formal_specification",
                "source_path": "Hyper-Systemizer Formal Specification.pdf",
            },
            policy=self.policy,
            verification_context={
                "receipt_verified": True,
                "ci_structural_test": True,
            },
        )
        self.assertEqual(standing, int(Standing.PROVEN))
        self.assertEqual(label, "proven")
        self.assertTrue(rule and rule.startswith("verify:"))

    def test_grant_proposal_is_denied(self):
        label, rule = resolve_claim_label(
            {
                "title": "Anchor_Connectome_Framework_Grant_Proposal_v2_1",
                "slug": "anchor_connectome_framework_grant_proposal_v2_1",
                "source_path": "Anchor_Connectome_Framework_Grant_Proposal_v2_1.pdf",
            },
            policy=self.policy,
        )
        self.assertEqual(label, "denied")
        self.assertTrue(rule and rule.startswith("deny:"))

    def test_linkedin_case_study_is_denied(self):
        label, rule = resolve_claim_label(
            {
                "title": "LinkedIn Lockout Case Study",
                "slug": "linkedin_lockout_case_study",
                "source_path": "LinkedIn Lockout Case Study.pdf",
            },
            policy=self.policy,
        )
        self.assertEqual(label, "denied")
        self.assertEqual(rule, "deny:linkedin_case")

    def test_fieldguide_operator_narrative_denied(self):
        label, rule = resolve_claim_label(
            {
                "title": "Chaos_Goblinus Taxonomia",
                "slug": "chaos_goblinus_taxonomia",
                "source_path": "docs/fieldguide/Chaos_Goblinus Taxonomia.pdf",
            },
            policy=self.policy,
        )
        self.assertEqual(label, "denied")
        self.assertEqual(rule, "deny:operator_narrative")

    def test_duplicate_flag_is_denied(self):
        label, rule = resolve_claim_label(
            {
                "title": "The Six Invariants",
                "slug": "the_six_invariants_copy",
                "source_path": "The Six Invariants (1).pdf",
                "duplicate_of": "six_invariants",
            },
            policy=self.policy,
        )
        self.assertEqual(label, "denied")
        self.assertEqual(rule, "deny:duplicate_of")

    def test_canonical_flag_no_longer_auto_proven(self):
        label, rule = resolve_claim_label(
            {
                "title": "The Six Invariants",
                "slug": "six_invariants",
                "source_path": "docs/fieldguide/The Six Invariants.pdf",
                "canonical": True,
            },
            policy=self.policy,
        )
        self.assertEqual(label, "hypothetical")
        self.assertTrue(rule and rule.startswith("hypothetical:"))

    def test_conceptual_architecture_stays_asserted(self):
        doc = {
            "claim_label": "asserted",
            "title": "AAIS - A Conceptual Architecture for Governed Cognitive Systems",
            "slug": "aais_a_conceptual_architecture_for_governed_cognitive_systems",
            "source_path": "AAIS - A Conceptual Architecture for Governed Cognitive Systems.pdf",
        }
        label, rule = resolve_claim_label(doc, policy=self.policy)
        self.assertEqual(label, "asserted")
        upgrade, target, _ = should_upgrade_claim_label(doc, policy=self.policy)
        self.assertFalse(upgrade)
        self.assertEqual(target, "asserted")

    def test_should_downgrade_proven_fieldguide_to_denied(self):
        doc = {
            "claim_label": "proven",
            "standing": 3,
            "title": "Chaos_Goblinus Taxonomia",
            "slug": "chaos_goblinus_taxonomia",
            "source_path": "docs/fieldguide/Chaos_Goblinus Taxonomia.pdf",
        }
        downgrade, target, rule = should_downgrade_claim_label(doc, policy=self.policy)
        self.assertTrue(downgrade)
        self.assertEqual(target, "denied")
        exclude, _ = should_exclude_from_library(doc, policy=self.policy)
        self.assertTrue(exclude)

    def test_no_upgrade_when_already_proven_with_verification(self):
        doc = {
            "claim_label": "proven",
            "standing": 3,
            "title": "Hyper-Systemizer Formal Specification",
            "slug": "hyper_systemizer_formal_specification",
            "source_path": "Hyper-Systemizer Formal Specification.pdf",
        }
        upgrade, target, rule = should_upgrade_claim_label(
            doc,
            policy=self.policy,
            verification_context={"receipt_verified": True, "ci_structural_test": True},
        )
        self.assertFalse(upgrade)

    def test_reward_calculator_standing_multipliers(self):
        profile = OperatorProfile(
            operator_id="op:test", tenant_id="tenant:test", reputation_score=0.0
        )
        receipt_hyp = {"payload": {"claim_label": "hypothetical", "standing": 1}}
        deltas_hyp = compute_deltas(EVENT_PROOF_PACKET_PUBLISHED, receipt_hyp, profile)
        self.assertIsNotNone(deltas_hyp)
        self.assertEqual(deltas_hyp["reputation"], 4.5)
        self.assertEqual(deltas_hyp["rail_credits"], 0.0)

        receipt_denied = {"payload": {"claim_label": "denied", "standing": 0}}
        self.assertIsNone(compute_deltas(EVENT_PROOF_PACKET_PUBLISHED, receipt_denied, profile))

        receipt_proven = {"payload": {"claim_label": "proven", "standing": 3}}
        deltas_proven = compute_deltas(EVENT_PROOF_PACKET_PUBLISHED, receipt_proven, profile)
        self.assertIsNotNone(deltas_proven)
        self.assertEqual(deltas_proven["reputation"], 58.0)
        self.assertEqual(deltas_proven["rail_credits"], 10.0)


if __name__ == "__main__":
    unittest.main()
