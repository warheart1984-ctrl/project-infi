"""Tests for federated civilizational epoch charter adoption (FCE-2)."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.federated_civilizational_epoch_registry import load_adopted_charters
from src.federated_civilizational_epoch_runtime import FederatedCivilizationalEpochRuntime
from src.governed_civilization_registry import save_adopted_civilization
from src.jarvis_federated_epoch_authority import authorize_federated_epoch_overlay_admission
from tests.fce_test_helpers import open_amendable_epoch_window


class FederatedCivilizationalEpochAdoptTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        os.environ["AAIS_OPERATOR_ORG_DOMAIN"] = "operator.example"
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        repo_root = Path(__file__).resolve().parents[1]
        shutil.copy(
            repo_root / "governance" / "operator_federated_epoch_registry.v1.json",
            gov / "operator_federated_epoch_registry.v1.json",
        )
        shutil.copy(
            repo_root / "governance" / "operator_civilization_registry.v1.json",
            gov / "operator_civilization_registry.v1.json",
        )
        open_amendable_epoch_window(gov / "operator_federated_epoch_registry.v1.json")
        save_adopted_civilization(
            {
                "civilization_id": "gcv_seed001",
                "summary": "Seed governed civilization for FCE upstream",
                "admitted_charter_ids": ["charter_a", "charter_b"],
            },
            repo_root=root,
        )
        self.runtime = FederatedCivilizationalEpochRuntime(
            runtime_dir=Path(self._tmpdir.name), repo_root=root
        )
        self.repo_root = root
        candidates = self.runtime.surface_epoch_candidates()
        self.assertTrue(candidates, "expected at least one epoch candidate")
        self.candidate = candidates[0]
        self.witnesses = [
            {
                "witness_id": "witness_peer_001",
                "witness_org_domain": "peer.example",
                "trust_bundle_ref": "trustbundle://peer.example/stage19/v1",
                "signed_at": "2026-06-07T12:00:00Z",
            }
        ]

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("AAIS_OPERATOR_ORG_DOMAIN", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_adopt_with_witness_quorum_and_dual_gate(self):
        auth = authorize_federated_epoch_overlay_admission(
            self.candidate, repo_root=self.repo_root
        )
        self.assertTrue(auth.get("authorized"))
        result = self.runtime.adopt_federated_epoch_charter(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            external_witnesses=self.witnesses,
            operator_org_domain="operator.example",
            session_id="fce-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        self.assertEqual(len(load_adopted_charters(runtime_dir=Path(self._tmpdir.name))), 1)
        self.assertTrue(self.runtime._overlay_path.is_file())

    def test_adopt_blocked_without_witness(self):
        auth = authorize_federated_epoch_overlay_admission(
            self.candidate, repo_root=self.repo_root
        )
        result = self.runtime.adopt_federated_epoch_charter(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            external_witnesses=[],
            operator_org_domain="operator.example",
        )
        self.assertEqual(result.get("outcome"), "blocked")
        self.assertEqual(result.get("reason"), "witness_quorum_failed")


if __name__ == "__main__":
    unittest.main()
