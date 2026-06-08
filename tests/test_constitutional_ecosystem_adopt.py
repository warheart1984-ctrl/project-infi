"""Tests for governed ecosystem charter adoption (CEC-2)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.constitutional_ecosystem_registry import adopted_charters
from src.constitutional_ecosystem_runtime import ConstitutionalEcosystemRuntime
from src.jarvis_ecosystem_authority import authorize_ecosystem_slot_admission


class ConstitutionalEcosystemAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        shutil.copy(
            Path(__file__).resolve().parents[1] / "governance" / "operator_ecosystem_registry.v1.json",
            gov / "operator_ecosystem_registry.v1.json",
        )
        self.runtime = ConstitutionalEcosystemRuntime(runtime_dir=Path(self._tmpdir.name), repo_root=root)
        self.candidate = {
            "candidate_id": "ecand_test001",
            "charter_kind": "federated_cluster",
            "summary": "Federated cluster charter for cross-organism ecosystem proof",
            "admitted_pact_ids": ["pact_a", "pact_b"],
            "admitted_norm_ids": [],
            "arbitration_policy": "operator_supervised",
            "stability_score": 0.85,
            "cec_class": "CEC-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_with_dual_gate(self):
        auth = authorize_ecosystem_slot_admission(self.candidate)
        result = self.runtime.adopt_ecosystem_charter(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="cec-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        self.assertEqual(len(adopted_charters(repo_root=Path(self._repo_tmp.name))), 1)
        self.assertTrue(self.runtime._overlay_path.is_file())


if __name__ == "__main__":
    unittest.main()
