"""Tests for governed charter amendment adoption (CEV-2)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.constitutional_evolution_registry import adopted_amendments
from src.constitutional_evolution_runtime import ConstitutionalEvolutionRuntime
from src.jarvis_constitutional_evolution_authority import authorize_amendment_overlay_admission


class ConstitutionalEvolutionAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1]
            / "governance"
            / "operator_constitutional_evolution_registry.v1.json",
            gov / "operator_constitutional_evolution_registry.v1.json",
        )
        self.runtime = ConstitutionalEvolutionRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.candidate = {
            "candidate_id": "amcand_test001",
            "charter_id": "charter_test001",
            "amendment_kind": "scope_extension",
            "tier5_tags": ["tier5_maturity", "contextual_gate", "dual_gate"],
            "summary": "Tier-5 contextual amendment extending charter scope",
            "cev_class": "CEV-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_with_dual_gate(self):
        auth = authorize_amendment_overlay_admission(self.candidate)
        result = self.runtime.adopt_charter_amendment(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="cev-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        self.assertEqual(len(adopted_amendments(repo_root=Path(self._repo_tmp.name))), 1)
        self.assertTrue(self.runtime._overlay_path.is_file())


if __name__ == "__main__":
    unittest.main()
