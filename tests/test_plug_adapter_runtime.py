"""Plug adapter runtime tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.plug_adapter_runtime import PlugAdapterRuntime


class PlugAdapterRuntimeTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["AAIS_RUNTIME_DIR"] = self._tmpdir.name
        self.runtime = PlugAdapterRuntime(runtime_dir=Path(self._tmpdir.name))

    def tearDown(self):
        os.environ.pop("AAIS_RUNTIME_DIR", None)
        self._tmpdir.cleanup()

    def test_registry_and_enable_execute(self):
        snap = self.runtime.registry_snapshot()
        self.assertGreater(snap["plug_count"], 0)
        plug_id = snap["plugs"][0]["plug_id"]
        self.runtime.set_plug_enabled(plug_id, True)
        result = self.runtime.execute_plug(plug_id, dry_run=True)
        self.assertIn("execution_id", result)


if __name__ == "__main__":
    unittest.main()
