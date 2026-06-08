"""Tests for workflow family registry and readiness."""

from __future__ import annotations

import unittest

from src.workflow_family_readiness import (
    compute_family_readiness,
    family_detail_with_readiness,
    list_families_with_readiness,
)
from src.workflow_family_registry import family_by_id, list_workflow_families


class WorkflowFamilyRegistryTests(unittest.TestCase):
    def test_six_families_present(self):
        families = list_workflow_families()
        self.assertEqual(len(families), 6)
        ids = {f.get("identity", {}).get("family_id") for f in families}
        self.assertIn("knowledge_work", ids)
        self.assertIn("personal_workflows", ids)

    def test_family_by_id(self):
        family = family_by_id("creative_workflows")
        self.assertIsNotNone(family)
        self.assertEqual(family["identity"]["family_id"], "creative_workflows")

    def test_readiness_rollups(self):
        organs = list_families_with_readiness()
        self.assertEqual(len(organs), 6)
        for organ in organs:
            self.assertIn("readiness", organ)
            self.assertIn("ready_chains", organ)
            self.assertIn("total_chains", organ)

    def test_family_detail_endpoint_shape(self):
        detail = family_detail_with_readiness("knowledge_work")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["identity"]["family_id"], "knowledge_work")
        self.assertIn("libraries", detail)
        self.assertIn("chains", detail)

    def test_compute_family_readiness_structure(self):
        family = family_by_id("data_workflows")
        self.assertIsNotNone(family)
        ready = compute_family_readiness(family)
        self.assertIn(ready["readiness"], {"ready", "partial", "prototype", "empty", "missing"})

    def test_handoff_graph(self):
        from src.workflow_family_registry import handoffs_for, list_handoff_edges, validate_handoff_graph

        errors = validate_handoff_graph()
        self.assertEqual(errors, [])
        self.assertGreaterEqual(len(list_handoff_edges()), 4)
        self.assertGreaterEqual(len(handoffs_for("knowledge_work")), 2)
