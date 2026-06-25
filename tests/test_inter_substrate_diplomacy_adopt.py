"""Tests for governed diplomatic accord adoption (ISD-2)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.diplomacy.registry import adopted_accords
from src.diplomacy.runtime import InterSubstrateDiplomacyRuntime
from src.jarvis_diplomacy_authority import authorize_diplomacy_overlay_admission


class InterSubstrateDiplomacyAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        (gov / "operator_diplomatic_registry.v1.json").write_text(
            json.dumps(
                {
                    "operator_diplomatic_registry_version": "operator_diplomatic_registry.v1",
                    "accords": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.runtime = InterSubstrateDiplomacyRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.candidate = {
            "candidate_id": "acand_test001",
            "accord_kind": "composite",
            "summary": "Diplomatic accord for federated substrate handoff",
            "substrate_scopes": ["ul_substrate", "memory_overlay", "imxp_envelope"],
            "consent_requirements": {"dual_consent": True},
            "stability_score": 0.82,
            "isd_class": "ISD-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_with_dual_gate(self):
        auth = authorize_diplomacy_overlay_admission(self.candidate)
        result = self.runtime.adopt_diplomatic_accord(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="isd-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        self.assertEqual(len(adopted_accords(repo_root=Path(self._repo_tmp.name))), 1)
        self.assertTrue(self.runtime._overlay_path.is_file())


if __name__ == "__main__":
    unittest.main()
