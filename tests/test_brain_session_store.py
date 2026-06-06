"""Brain session store tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.brain_session_store import BrainSessionStore


class BrainSessionStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.store = BrainSessionStore(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_create_and_decide(self):
        session = self.store.create_session("research topic")
        self.assertEqual(session["operator_decision"], "pending")
        updated = self.store.decide(session["session_id"], "accept")
        self.assertEqual(updated["operator_decision"], "accepted")


if __name__ == "__main__":
    unittest.main()
