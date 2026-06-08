"""Tests for governed civilization charter adoption (GCV-2)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.governed_civilization_registry import adopted_civilizations
from src.governed_civilization_runtime import GovernedCivilizationRuntime
from src.jarvis_civilization_authority import authorize_civilization_overlay_admission


class GovernedCivilizationAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_civilization_registry.v1.json",
            gov / "operator_civilization_registry.v1.json",
        )
        self.runtime = GovernedCivilizationRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.candidate = {
            "candidate_id": "cvcand_test001",
            "summary": "Governed civilization binding multiple ecosystem charters",
            "admitted_charter_ids": ["charter_a", "charter_b"],
            "admitted_accord_ids": [],
            "admitted_treaty_ids": [],
            "stability_score": 0.88,
            "gcv_class": "GCV-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_with_dual_gate(self):
        auth = authorize_civilization_overlay_admission(self.candidate)
        result = self.runtime.adopt_civilization_charter(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="gcv-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        self.assertEqual(len(adopted_civilizations(repo_root=Path(self._repo_tmp.name))), 1)
        self.assertTrue(self.runtime._overlay_path.is_file())


if __name__ == "__main__":
    unittest.main()
