"""Tests for Human–AI Charter operator surfaces (Art IV / Art V)."""

from __future__ import annotations

import unittest

from src.human_ai_charter_surfaces import (
    attach_charter_surfaces,
    build_collaboration_options,
    build_epistemic_perimeter,
)


class HumanAiCharterSurfacesTests(unittest.TestCase):
    def test_epistemic_perimeter_escalates_on_attention(self):
        perimeter = build_epistemic_perimeter(
            domain="inter_substrate_diplomacy",
            declared_scopes=["ul_substrate"],
            drift_events=[
                {"drift_id": "d1", "severity": "attention", "source": "test", "summary": "insufficient evidence"}
            ],
            upstream_evidence_count=0,
        )
        self.assertEqual(perimeter["charter_article"], "IV")
        self.assertTrue(perimeter["escalation_required"])
        self.assertTrue(perimeter["ai_cannot_expand_scope"])

    def test_collaboration_options_requires_multiple_paths(self):
        options = build_collaboration_options(
            domain="norm_federation",
            candidates=[{"candidate_id": "c1", "summary": "Treaty A", "stability_score": 0.8}],
        )
        self.assertEqual(options["charter_article"], "V")
        self.assertGreaterEqual(len(options["options"]), 2)
        self.assertTrue(options["single_path_blocked"])

    def test_attach_charter_surfaces(self):
        payload = attach_charter_surfaces(
            {"outcome": "observed"},
            domain="inter_substrate_diplomacy",
            declared_scopes=["memory_overlay"],
            drift_events=[],
            upstream_evidence_count=1,
            candidates=[],
        )
        self.assertIn("charter_surfaces", payload)
        self.assertIn("epistemic_perimeter", payload["charter_surfaces"])
        self.assertIn("collaboration_options", payload["charter_surfaces"])


if __name__ == "__main__":
    unittest.main()
