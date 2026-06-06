"""Brain proposal validator tests."""

from __future__ import annotations

import unittest

from src.brain_proposal_validator import build_brain_proposal, validate_brain_proposal


class BrainProposalValidatorTests(unittest.TestCase):
    def test_build_and_validate(self):
        proposal = build_brain_proposal("research a topic and draft a brief")
        self.assertEqual(proposal["status"], "proposal_only")
        self.assertEqual(proposal["routing"]["organ_rankings"][0]["family_id"], "knowledge_work")
        self.assertFalse(validate_brain_proposal(proposal))


if __name__ == "__main__":
    unittest.main()
