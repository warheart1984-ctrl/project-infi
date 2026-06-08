"""Tests for epoch-bound constitutional amendment windows (CEV + FCE)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("AAIS_GENOME_BOOT", "warn")

from src.constitutional_evolution_runtime import (
    ConstitutionalEvolutionRuntime,
    validate_amendment_epoch_window,
)
from src.federated_civilizational_epoch_registry import is_epoch_amendable
from src.jarvis_constitutional_evolution_authority import authorize_amendment_overlay_admission
from tests.fce_test_helpers import open_amendable_epoch_window


class EpochAmendmentWindowTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._repo_tmp = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        root = Path(self._repo_tmp.name)
        gov = root / "governance"
        gov.mkdir(parents=True)
        repo_root = Path(__file__).resolve().parents[1]
        shutil.copy(
            repo_root / "governance" / "operator_constitutional_evolution_registry.v1.json",
            gov / "operator_constitutional_evolution_registry.v1.json",
        )
        shutil.copy(
            repo_root / "governance" / "operator_federated_epoch_registry.v1.json",
            gov / "operator_federated_epoch_registry.v1.json",
        )
        self.epoch_id = open_amendable_epoch_window(
            gov / "operator_federated_epoch_registry.v1.json",
            epoch_id="epoch_pilot_001",
        )
        self.repo_root = root
        self.runtime = ConstitutionalEvolutionRuntime(
            runtime_dir=Path(self._tmpdir.name), repo_root=root
        )
        self.candidate = {
            "candidate_id": "amcand_epoch001",
            "charter_id": "charter_test001",
            "epoch_id": "epoch_pilot_001",
            "amendment_kind": "scope_extension",
            "tier5_tags": ["tier5_maturity", "contextual_gate", "dual_gate"],
            "summary": "Epoch-bound amendment within pilot window",
            "cev_class": "CEV-1",
        }

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()
        self._repo_tmp.cleanup()

    def test_amendable_within_pilot_window(self):
        reg_path = self.repo_root / "governance" / "operator_federated_epoch_registry.v1.json"
        doc = json.loads(reg_path.read_text(encoding="utf-8"))
        epoch = next(
            e for e in doc.get("epochs") or [] if str(e.get("epoch_id")) == "epoch_pilot_001"
        )
        start = datetime.fromisoformat(str(epoch["epoch_start_utc"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(epoch["epoch_end_utc"]).replace("Z", "+00:00"))
        mid_pilot = start + (end - start) / 2
        check = is_epoch_amendable("epoch_pilot_001", repo_root=self.repo_root, now=mid_pilot)
        self.assertTrue(check.get("amendable"))

    def test_amendment_blocked_when_epoch_frozen(self):
        reg_path = self.repo_root / "governance" / "operator_federated_epoch_registry.v1.json"
        doc = json.loads(reg_path.read_text(encoding="utf-8"))
        doc["epochs"][0]["frozen"] = True
        reg_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        validation = validate_amendment_epoch_window(self.candidate, repo_root=self.repo_root)
        self.assertFalse(validation.get("aligned"))
        auth = authorize_amendment_overlay_admission(self.candidate, repo_root=self.repo_root)
        result = self.runtime.adopt_charter_amendment(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="epoch-window-test",
        )
        self.assertEqual(result.get("outcome"), "blocked")

    def test_amendment_adopts_with_epoch_id(self):
        auth = authorize_amendment_overlay_admission(self.candidate, repo_root=self.repo_root)
        result = self.runtime.adopt_charter_amendment(
            self.candidate,
            operator_approved=True,
            jarvis_authorization=auth,
            session_id="epoch-window-test",
        )
        self.assertEqual(result.get("outcome"), "adopted")
        amendment = result.get("amendment") or {}
        self.assertEqual(amendment.get("epoch_id"), "epoch_pilot_001")


if __name__ == "__main__":
    unittest.main()
