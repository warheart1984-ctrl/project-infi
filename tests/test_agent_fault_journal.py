"""Tests for agent fault journal."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.agent_fault_journal import AgentFaultJournal


class TestAgentFaultJournal(unittest.TestCase):
    def test_record_appends_ndjson(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "faults.ndjson"
            journal = AgentFaultJournal(path=path)
            entry = journal.record(
                run_id="run_test",
                phase="output",
                input_ref="goal hash",
                output_ref="error hash",
                fault_code="SCOPE_CREEP",
            )
            self.assertEqual(entry["fault_code"], "SCOPE_CREEP")
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["run_id"], "run_test")


if __name__ == "__main__":
    unittest.main()
