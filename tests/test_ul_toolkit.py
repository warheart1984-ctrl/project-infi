"""Tests for the AAIS-UL diagnostic toolkit."""

import json
import unittest
from pathlib import Path

from tools.ul._common import FIXTURES_DIR, PROJECT_ROOT
from tools.ul.drift import collect_adapter_sections
from tools.ul.probe import probe_payload
from tools.ul.scan import scan_paths
from tools.ul.smoke import run_smoke


class TestULToolkit(unittest.TestCase):
    def test_probe_forge_fixture(self):
        payload = json.loads((FIXTURES_DIR / "forge_contractor_ok.json").read_text(encoding="utf-8"))
        report = probe_payload(payload, wrap=True)
        self.assertEqual(report["primary_section"], "tool_results")
        self.assertTrue(report["wrapped"]["has_ul_substrate"])

    def test_probe_patch_plan_fixture(self):
        payload = json.loads((FIXTURES_DIR / "patch_plan.json").read_text(encoding="utf-8"))
        report = probe_payload(payload)
        self.assertEqual(report["primary_section"], "proposal_state")

    def test_scan_src_finds_wired_files(self):
        report = scan_paths([PROJECT_ROOT / "src" / "cognitive_bridge.py"])
        self.assertEqual(report["wired_file_count"], 1)

    def test_smoke_samples(self):
        report = run_smoke(wrap=True, run_pytest=False)
        self.assertEqual(report["failed_samples"], 0)

    def test_drift_report_shape(self):
        report = collect_adapter_sections()
        self.assertIn("doctrine_sections", report)
        self.assertGreaterEqual(report["adapter_count"], 40)


if __name__ == "__main__":
    unittest.main()
