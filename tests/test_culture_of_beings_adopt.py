"""Tests for governed shared norm adoption (COB-2)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.culture_of_beings_registry import adopted_norms
from src.culture_of_beings_runtime import CultureOfBeingsRuntime
from src.jarvis_culture_of_beings_authority import authorize_culture_of_beings_slot_admission


class CultureOfBeingsAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_culture_of_beings_registry.v1.json",
            gov / "operator_culture_of_beings_registry.v1.json",
        )
        self.runtime = CultureOfBeingsRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.candidate = {
            "candidate_id": "ncand_test001",
            "norm_kind": "handoff_ritual",
            "summary": "Cross-organism handoff ritual for federated mesh proof",
            "cluster_ref": {"grant_id": "grant-test"},
            "continuity_posture": "governed_cluster",
            "trust_tier": "governed_cluster",
            "evidence_refs": ["mesh:proof"],
            "stability_score": 0.8,
            "cob_class": "COB-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_blocked_without_operator(self):
        auth = authorize_culture_of_beings_slot_admission(self.candidate)
        result = self.runtime.adopt_shared_norm(self.candidate, operator_approved=False, jarvis_authorization=auth)
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(len(adopted_norms(repo_root=Path(self._repo_tmp.name))), 0)

    def test_adopt_with_dual_gate(self):
        auth = authorize_culture_of_beings_slot_admission(self.candidate)
        result = self.runtime.adopt_shared_norm(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="cob-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        self.assertEqual(len(adopted_norms(repo_root=Path(self._repo_tmp.name))), 1)
        self.assertTrue(self.runtime._overlay_path.is_file())


if __name__ == "__main__":
    unittest.main()
