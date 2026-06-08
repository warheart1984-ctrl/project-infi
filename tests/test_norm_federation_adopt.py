"""Tests for governed norm federation treaty adoption (NFD-2)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.jarvis_norm_federation_authority import authorize_norm_federation_overlay_admission
from src.norm_federation_registry import adopted_treaties
from src.norm_federation_runtime import NormFederationRuntime


class NormFederationAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_norm_federation_registry.v1.json",
            gov / "operator_norm_federation_registry.v1.json",
        )
        self.runtime = NormFederationRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.candidate = {
            "candidate_id": "tcand_test001",
            "treaty_kind": "cluster_norm",
            "summary": "Federation treaty linking cluster norms across ecosystems",
            "adopted_norm_ids": ["norm_a", "norm_b"],
            "stability_score": 0.8,
            "nfd_class": "NFD-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_with_dual_gate(self):
        auth = authorize_norm_federation_overlay_admission(self.candidate)
        result = self.runtime.adopt_federation_treaty(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="nfd-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        self.assertEqual(len(adopted_treaties(repo_root=Path(self._repo_tmp.name))), 1)
        self.assertTrue(self.runtime._overlay_path.is_file())


if __name__ == "__main__":
    unittest.main()
