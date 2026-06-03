"""v2.2 observed Cloud Forge ledger linkage on mission open."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.mission.mission_runtime import UGRMissionRuntime


class TestCloudForgeObservedMission(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(tempfile.mkdtemp(prefix="ugr-cf-obs-"))
        self.ledger_path = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "proof"
            / "cloud-forge"
            / "rail-decisions.jsonl"
        )
        self.ledger_backup = None
        if self.ledger_path.exists():
            self.ledger_backup = self.ledger_path.read_text(encoding="utf-8")
        os.environ["AAIS_RUNTIME_DIR"] = str(self.temp_root)
        os.environ["UGR_CLOUD_FORGE_OBSERVED"] = "1"
        os.environ["CLOUD_FORGE_LEDGER_PATH"] = str(
            self.temp_root / "cloud-forge" / "rail-decisions.jsonl"
        )
        os.environ["URG_OPERATOR_RECEIPT_KEY"] = "cf-obs-op"
        os.environ["URG_RECEIPT_SIGNING_KEY"] = "cf-obs-urg"
        demo_path = Path(__file__).resolve().parents[1] / "deploy" / "ugr" / "mission-demo.json"
        self.demo = json.loads(demo_path.read_text(encoding="utf-8"))["mission"]

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        os.environ.pop("UGR_CLOUD_FORGE_OBSERVED", None)
        os.environ.pop("CLOUD_FORGE_LEDGER_PATH", None)
        os.environ.pop("URG_OPERATOR_RECEIPT_KEY", None)
        os.environ.pop("URG_RECEIPT_SIGNING_KEY", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)
        if self.ledger_backup is not None:
            self.ledger_path.write_text(self.ledger_backup, encoding="utf-8")

    def test_mission_observed_ledger_row_matches_tenant(self):
        result = UGRMissionRuntime(runtime_dir=self.temp_root).run_mission(self.demo)
        self.assertEqual(result["status"], "ok")
        ingress = result.get("urg_ingress") or {}
        self.assertEqual(ingress.get("cloud_forge_binding_version"), "3.0")
        ledger_file = self.temp_root / "cloud-forge" / "rail-decisions.jsonl"
        self.assertTrue(ledger_file.exists())
        rows = [
            json.loads(line)
            for line in ledger_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertTrue(rows)
        last = rows[-1]
        self.assertEqual(last.get("tenant_id"), "tenant-acme")


if __name__ == "__main__":
    unittest.main()
