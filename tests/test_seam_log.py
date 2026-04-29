"""Tests for the shared AAIS seam log."""

from pathlib import Path
import shutil
import tempfile
import unittest

from src.seam_log import list_seam_events, record_seam_event, reset_seam_log


class TestSeamLog(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="seam-log-"))
        reset_seam_log(runtime_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_recorded_events_append_in_order(self):
        first = record_seam_event(
            classification="seam",
            source="test_detector",
            boundary="runtime_boundary",
            reason="First seam was detected.",
            runtime_dir=self.temp_dir,
        )
        second = record_seam_event(
            classification="boundary_violation",
            source="test_detector",
            boundary="memory_gateway",
            reason="Second seam was blocked.",
            decision="BLOCK",
            vector="missing_attestation",
            runtime_dir=self.temp_dir,
        )

        events = list_seam_events(runtime_dir=self.temp_dir, limit=10)

        self.assertEqual([item["event_id"] for item in events], [first["event_id"], second["event_id"]])
        self.assertEqual(events[-1]["decision"], "BLOCK")
        self.assertEqual(events[-1]["vector"], "missing_attestation")


if __name__ == "__main__":
    unittest.main()
