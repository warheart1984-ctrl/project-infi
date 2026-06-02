from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from triangulation.common import FIXTURE_ROOT
from triangulation.correlate import correlate_case, load_triangulation
from triangulation.normalize import (
    normalize_mechanic_claims,
    normalize_scorpion_claims,
)


class TestTriangulation(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="triangulation_test_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_fixture_correlates_with_proven_edge(self) -> None:
        payload = correlate_case(
            "tri-demo-001",
            triangulation_root=self.temp_root,
            fixture_root=FIXTURE_ROOT / "tri-demo-001",
        )
        self.assertEqual(payload["triangulation_version"], "triangulation.v1")
        self.assertGreaterEqual(len(payload["claims"]), 2)
        self.assertGreaterEqual(len(payload["correlation_edges"]), 1)
        proven = [
            edge
            for edge in payload["correlation_edges"]
            if edge.get("correlation_type") == "invariant_overlap"
            and edge.get("claim_label") == "proven"
        ]
        self.assertTrue(proven, "expected proven invariant_overlap edge")
        self.assertTrue(payload.get("launch_blocked"))
        loaded = load_triangulation("tri-demo-001", runtime_root=self.temp_root)
        self.assertEqual(loaded["case_id"], "tri-demo-001")

    def test_normalize_mechanic_claims(self) -> None:
        fixture_ledger = FIXTURE_ROOT / "tri-demo-001" / "mechanic_diagnostic_ledger.jsonl"
        claims = normalize_mechanic_claims(ledger_path=fixture_ledger, case_id="tri-demo-001")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["source"], "mechanic")
        self.assertEqual(claims[0]["invariant_id"], "GOV-CI-03")

    def test_normalize_scorpion_claims(self) -> None:
        fixture_ledger = FIXTURE_ROOT / "tri-demo-001" / "scorpion_anomaly_ledger.jsonl"
        claims = normalize_scorpion_claims(ledger_path=fixture_ledger, case_id="tri-demo-001")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["invariant_id"], "fd_flow")

    def test_missing_source_stays_asserted(self) -> None:
        empty_fix = self.temp_root / "empty-fix"
        empty_fix.mkdir()
        (empty_fix / "mechanic_diagnostic_ledger.jsonl").write_text("", encoding="utf-8")
        payload = correlate_case(
            "tri-empty-001",
            triangulation_root=self.temp_root / "out",
            fixture_root=empty_fix,
        )
        self.assertEqual(payload["claim_label"], "asserted")
        self.assertEqual(len(payload["claims"]), 0)


if __name__ == "__main__":
    unittest.main()
