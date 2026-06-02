"""Lab cross-machine replay tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lab.replay import run_lab_replay


class TestLabReplay(unittest.TestCase):
    def test_replay_runs_manifest_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "manifest_version": "lab.cross_machine.v1",
                        "operational_status": "active_single_machine",
                        "commands": ["python -c \"print('lab-replay-ok')\""],
                    }
                ),
                encoding="utf-8",
            )
            report = run_lab_replay(manifest_path=manifest, repo_root=root)
            self.assertTrue(report["passed"])
            self.assertTrue(report["result_hash"])


if __name__ == "__main__":
    unittest.main()
